"""
PDF財務諸表読み取りサービス
PDFをアップロードしてテキスト抽出し、LLMで各項目を解析する
"""
import os
import json
import pdfplumber
from openai import OpenAI

# 使用するモデル
MODEL = "gpt-4.1-mini"


def get_openai_client(api_key: str = None) -> OpenAI:
    """
    OpenAIクライアントを取得する。
    優先順位: 引数api_key > 環境変数OPENAI_API_KEY
    """
    if api_key:
        return OpenAI(api_key=api_key)
    # 環境変数から取得（デフォルト）
    return OpenAI()


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDFからテキストを抽出する"""
    text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text_pages.append(f"=== ページ {i+1} ===\n{page_text}")
    return "\n\n".join(text_pages)


def parse_original_and_meta(pdf_text: str, api_key: str = None) -> dict:
    """
    1回のAPI呼び出しで以下を一括取得：
    - 金額単位（円/千円/百万円）
    - 含まれる財務諸表の種類
    - 試算表の生科目データ（PL/BS/製造原価）
    
    Returns:
        {
            "unit": "円",
            "detected_types": ["profit_loss", "balance_sheet", "manufacturing_cost"],
            "pl_items": [{"name": "売上高", "amount": 394238924}, ...],
            "bs_items": [{"name": "現金及び預金", "amount": 12345678}, ...],
            "mcr_items": [{"name": "[製]外注加工費", "amount": 209540169}, ...]
        }
    """
    client = get_openai_client(api_key)

    prompt = f"""以下は財務諸表PDFから抽出したテキストです。
次の情報をすべて一括で読み取り、指定のJSONフォーマットで返してください。

【読み取り内容】
1. 金額単位の判定（"円" / "千円" / "百万円"）
2. 含まれる財務諸表の種類（profit_loss/balance_sheet/manufacturing_cost）
3. 試算表の全科目と金額（生データをそのまま）

【重要なルール】
- 金額単位が「円」の場合：カンマや空白を除去して円単位の整数をそのまま返す
- 金額単位が「千円」の場合：1000を掛けて円単位に変換して返す
- 金額単位が「百万円」の場合：1000000を掛けて円単位に変換して返す
- 科目名はPDFに記載されている名称をそのまま使用する（例：「[製]外注加工費」「売上高」など）
- 金額は期間残高（または期末残高）の値を使用する
- 合計行（「合計」「計」で終わる科目）も含める
- 損益計算書・製造原価報告書・貸借対照表の3種類に分類する
- 製造原価報告書の科目は「[製]」プレフィックスがある場合はそのまま含める
- PDFに記載されている科目はすべて含める（金額がゼロの科目も必ず含める）
- 貸借対照表の有形固定資産の明細科目（建物、構築物、機械装置、工具器具備品、車両運搬具、土地、建設仮勘定など）は必ず個別に含める
- 損益計算書の営業外収益・営業外費用の明細科目（受取利息、受取配当金、支払利息、雑収入、雑損失など）は必ず個別に含める
- 各科目の金額は必ずその科目自身の金額を使用する。隣接する行や合計行の金額を誤って割り当てないこと
- 各科目に「section」フィールドを付与する：PDFのセクション見出し（「流動資産」「固定資産」「流動負債」「固定負債」「純資産」「売上高」「売上原価」「販売費及び一般管理費」「営業外収益」「営業外費用」「特別利益」「特別損失」など）をそのまま記載する

【出力フォーマット（JSON）】
{{
  "unit": "円",
  "detected_types": ["profit_loss", "balance_sheet", "manufacturing_cost"],
  "pl_items": [
    {{"name": "売上高", "amount": 394238924, "section": "売上高"}},
    {{"name": "売上原価", "amount": 259960759, "section": "売上原価"}},
    ...
  ],
  "bs_items": [
    {{"name": "現金", "amount": 399038, "section": "流動資産"}},
    {{"name": "売掛金", "amount": 5678901, "section": "流動資産"}},
    ...
  ],
  "mcr_items": [
    {{"name": "[製]外注加工費", "amount": 209540169, "section": "製造原価"}},
    {{"name": "[製]荷造運費", "amount": 69, "section": "製造原価"}},
    ...
  ]
}}

【PDFテキスト】
{pdf_text}

JSONのみを返してください。説明文は不要です。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    # 各itemのamountを整数に変換
    for key in ['pl_items', 'bs_items', 'mcr_items']:
        if key in result and isinstance(result[key], list):
            for item in result[key]:
                if 'amount' in item:
                    try:
                        item['amount'] = int(item['amount']) if item['amount'] else 0
                    except (ValueError, TypeError):
                        item['amount'] = 0

    return result


def parse_restructured_data(pdf_text: str, api_key: str = None, unit: str = "円") -> dict:
    """
    1回のAPI呼び出しでBS・PL・製造原価の組換え用データを一括取得
    
    Returns:
        {
            "balance_sheet": {...},
            "profit_loss": {...},
            "manufacturing_cost": {...}
        }
    """
    client = get_openai_client(api_key)

    unit_instruction = {
        "円": "- 金額は「円」単位で記載されています。カンマや空白を除去して円単位の整数をそのまま返す（例: 1,234,000円 → 1234000）",
        "千円": "- 金額は「千円」単位で記載されています。1000を掛けて円単位の整数に変換して返す（例: 1,234千円 → 1234000）",
        "百万円": "- 金額は「百万円」単位で記載されています。1000000を掛けて円単位の整数に変換して返す（例: 1,234百万円 → 1234000000）",
    }.get(unit, "- 金額はそのまま整数で返す")

    prompt = f"""以下は財務諸表PDFから抽出したテキストです。
貸借対照表・損益計算書・製造原価報告書の数値を読み取り、指定のJSONフォーマットで返してください。

【重要なルール】
{unit_instruction}
- 該当する項目が見つからない場合は 0 を返す
- カンマや円マークは除去して純粋な整数を返す
- 費用項目は正の整数で返す（マイナスにしない）

【出力フォーマット（JSON）】
{{
  "balance_sheet": {{
    "cash_on_hand": <手許現預金・現金及び預金>,
    "investment_deposits": <運用預金（定期預金等）>,
    "marketable_securities": <有価証券>,
    "trade_receivables": <売掛債権（売掛金＋受取手形の合計）>,
    "inventory_assets": <棚卸資産（商品・製品・仕掛品・原材料等の合計）>,
    "current_assets": <流動資産合計>,
    "tangible_fixed_assets": <有形固定資産合計>,
    "intangible_fixed_assets": <無形固定資産合計>,
    "investments_and_other": <投資その他の資産合計>,
    "deferred_assets": <繰延資産>,
    "fixed_assets": <固定資産合計>,
    "total_assets": <資産合計>,
    "trade_payables": <買掛債務（買掛金＋支払手形の合計）>,
    "short_term_borrowings": <短期借入金>,
    "current_portion_long_term": <1年以内返済長期借入金>,
    "discounted_notes": <割引手形>,
    "other_current_liabilities": <その他流動負債>,
    "current_liabilities": <流動負債合計>,
    "long_term_borrowings": <長期借入金>,
    "executive_borrowings": <役員等借入金>,
    "retirement_benefit_liability": <退職給付引当金>,
    "other_fixed_liabilities": <その他固定負債>,
    "fixed_liabilities": <固定負債合計>,
    "total_liabilities": <負債合計>,
    "capital": <資本金>,
    "capital_surplus": <資本剰余金>,
    "retained_earnings": <利益剰余金合計>,
    "legal_reserve_bs": <利益準備金>,
    "voluntary_reserve_bs": <任意積立金>,
    "retained_earnings_carried": <繰越利益剰余金>,
    "treasury_stock": <自己株式（負の値の場合も正の整数で返す）>,
    "net_assets": <純資産合計>,
    "total_liabilities_and_net_assets": <負債純資産合計>
  }},
  "profit_loss": {{
    "sales": <売上高>,
    "beginning_inventory": <期首棚卸高（製品・商品）>,
    "manufacturing_cost": <当期製造（工事）原価>,
    "ending_inventory": <期末棚卸高（製品・商品）>,
    "cost_of_sales": <売上原価合計>,
    "gross_profit": <売上総利益>,
    "labor_cost": <人件費（製造原価報告書の労務費＋販管費の人件費）>,
    "executive_compensation": <役員報酬>,
    "capital_regeneration_cost": <資本再生費（減価償却費＋修繕費）>,
    "research_development_expenses": <研究開発費>,
    "general_expenses": <一般経費>,
    "general_expenses_fixed": <一般経費のうち固定費>,
    "general_expenses_variable": <一般経費のうち変動費>,
    "selling_general_admin_expenses": <販売費及び一般管理費合計>,
    "operating_income": <営業利益>,
    "financial_profit_loss": <金融損益（受取利息＋受取配当金－支払利息）>,
    "other_non_operating": <その他の営業外損益>,
    "ordinary_income": <経常利益>,
    "extraordinary_profit_loss": <特別損益（特別利益－特別損失）>,
    "income_before_tax": <税引前当期純利益>,
    "income_taxes": <法人税等>,
    "net_income": <当期純利益>,
    "dividend": <配当金>,
    "retained_profit": <内部留保>,
    "legal_reserve": <利益準備金積立額>,
    "voluntary_reserve": <その他剰余金積立額>,
    "retained_earnings_increase": <繰越利益剰余金増加>
  }},
  "manufacturing_cost": {{
    "beginning_raw_material": <期首原材料棚卸高>,
    "raw_material_purchase": <当期原材料仕入高>,
    "ending_raw_material": <期末原材料棚卸高>,
    "material_cost": <材料費計（期首＋仕入－期末）>,
    "labor_cost_manufacturing": <労務費計（製造）>,
    "outsourcing_cost": <外注加工費（[製]外注加工費）>,
    "freight_manufacturing": <荷造運賃（製造）>,
    "meeting_cost_manufacturing": <会議費（製造）>,
    "travel_cost_manufacturing": <旅費交通費（製造）>,
    "communication_cost_manufacturing": <通信費（製造）>,
    "supplies_manufacturing": <消耗品費（製造）>,
    "vehicle_cost_manufacturing": <車両費（製造）>,
    "rent_manufacturing": <賃借料（製造）>,
    "insurance_manufacturing": <保険料（製造）>,
    "depreciation_manufacturing": <減価償却費（製造）>,
    "repair_cost_manufacturing": <修繕費（製造）>,
    "other_manufacturing_cost": <その他製造経費（上記以外の製造経費合計）>,
    "manufacturing_expenses_total": <製造経費計>,
    "total_manufacturing_cost_current": <総製造費用（材料費＋労務費＋製造経費の合計）>,
    "beginning_wip": <期首仕掛品棚卸高>,
    "ending_wip": <期末仕掛品棚卸高>,
    "total_manufacturing_cost": <製造原価合計（総製造費用＋期首仕掛品－期末仕掛品）>
  }}
}}

【PDFテキスト】
{pdf_text}

JSONのみを返してください。説明文は不要です。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    # 各サブセクションのフィールドを整数に変換
    for section in ['balance_sheet', 'profit_loss', 'manufacturing_cost']:
        if section in result and isinstance(result[section], dict):
            result[section] = {k: int(v) if v else 0 for k, v in result[section].items()}

    return result


def parse_financial_pdf(pdf_path: str, target_types: list = None, api_key: str = None) -> dict:
    """
    PDFを解析して財務諸表データを返す（最適化版：API呼び出し2回）

    Args:
        pdf_path: PDFファイルのパス
        target_types: 解析対象の種類リスト（None の場合は自動検出）
                      例: ["balance_sheet", "profit_loss", "manufacturing_cost"]

    Returns:
        {
            "detected_types": [...],
            "unit": "円",
            "balance_sheet": {...} or None,
            "profit_loss": {...} or None,
            "manufacturing_cost": {...} or None,
            "original_trial_balance": {
                "pl_items": [...],
                "bs_items": [...],
                "mcr_items": [...]
            },
            "raw_text": "..."
        }
    """
    # テキスト抽出
    pdf_text = extract_text_from_pdf(pdf_path)

    if not pdf_text.strip():
        return {
            "error": "PDFからテキストを抽出できませんでした。スキャンされたPDFの場合はOCRが必要です。",
            "detected_types": [],
            "unit": "円",
            "balance_sheet": None,
            "profit_loss": None,
            "manufacturing_cost": None,
            "original_trial_balance": None,
            "raw_text": ""
        }

    # 1回目のAPI呼び出し：単位検出 + 種類検出 + オリジナルデータ一括取得
    try:
        meta_result = parse_original_and_meta(pdf_text, api_key=api_key)
        unit = meta_result.get("unit", "円")
        detected_types = meta_result.get("detected_types", [])
        original_trial_balance = {
            "pl_items": meta_result.get("pl_items", []),
            "bs_items": meta_result.get("bs_items", []),
            "mcr_items": meta_result.get("mcr_items", [])
        }
    except Exception as e:
        unit = "円"
        detected_types = []
        original_trial_balance = None

    if target_types is not None:
        detected_types = target_types

    result = {
        "detected_types": detected_types,
        "unit": unit,
        "balance_sheet": None,
        "profit_loss": None,
        "manufacturing_cost": None,
        "original_trial_balance": original_trial_balance,
        "raw_text": pdf_text  # 再読み取り用（全テキスト）
    }

    # 2回目のAPI呼び出し：組換え用データを一括取得
    try:
        restructured = parse_restructured_data(pdf_text, api_key=api_key, unit=unit)
        if "balance_sheet" in detected_types:
            result["balance_sheet"] = restructured.get("balance_sheet")
        if "profit_loss" in detected_types:
            result["profit_loss"] = restructured.get("profit_loss")
        if "manufacturing_cost" in detected_types:
            result["manufacturing_cost"] = restructured.get("manufacturing_cost")
    except Exception as e:
        result["restructured_error"] = str(e)

    return result


def reparse_with_instruction(pdf_text: str, current_items: dict, additional_instruction: str, api_key: str = None) -> dict:
    """
    追加指示付きで試算表の生科目データを再読み取りする。
    
    Args:
        pdf_text: PDFから抽出したテキスト
        current_items: 現在の読み取り結果 {"bs_items": [...], "pl_items": [...], "mcr_items": [...]}
        additional_instruction: ユーザーからの追加指示文章
        api_key: OpenAI APIキー
    
    Returns:
        {"bs_items": [...], "pl_items": [...], "mcr_items": [...]}
    """
    client = get_openai_client(api_key)

    import json as _json
    current_bs = _json.dumps(current_items.get('bs_items', []), ensure_ascii=False)
    current_pl = _json.dumps(current_items.get('pl_items', []), ensure_ascii=False)
    current_mcr = _json.dumps(current_items.get('mcr_items', []), ensure_ascii=False)

    prompt = f"""以下は財務諸表PDFから抽出したテキストと、現在の読み取り結果です。
ユーザーからの追加指示に従って、読み取り結果を修正・補完してください。

【ユーザーからの追加指示】
{additional_instruction}

【現在の読み取り結果（貸借対照表科目）】
{current_bs}

【現在の読み取り結果（損益計算書科目）】
{current_pl}

【現在の読み取り結果（製造原価報告書科目）】
{current_mcr}

【重要なルール】
- 追加指示に従って修正・追加・削除を行う
- 科目名はPDFに記載されている名称をそのまま使用する
- 金額は円単位の整数で返す
- 各科目に「section」フィールドを付与する
- 修正が必要ない科目は現在の値をそのまま維持する
- PDFテキストを参照して正確な金額を読み取る

【出力フォーマット（JSON）】
{{
  "bs_items": [{{
    "name": "科目名",
    "amount": 123456,
    "section": "セクション名"
  }}],
  "pl_items": [{{
    "name": "科目名",
    "amount": 123456,
    "section": "セクション名"
  }}],
  "mcr_items": [{{
    "name": "科目名",
    "amount": 123456,
    "section": "セクション名"
  }}]
}}

【PDFテキスト】
{pdf_text}

JSONのみを返してください。説明文は不要です。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = _json.loads(response.choices[0].message.content)

    # 各itemのamountを整数に変換
    for key in ['pl_items', 'bs_items', 'mcr_items']:
        if key in result and isinstance(result[key], list):
            for item in result[key]:
                if 'amount' in item:
                    try:
                        item['amount'] = int(item['amount']) if item['amount'] else 0
                    except (ValueError, TypeError):
                        item['amount'] = 0

    return result


# ==================== 後方互換性のための旧関数（非推奨） ====================

def detect_unit(pdf_text: str, api_key: str = None) -> str:
    """PDFの金額単位を検出する（後方互換性のため残す）"""
    client = get_openai_client(api_key)
    prompt = f"""以下の財務諸表PDFテキストの金額単位を判定してください。
判定ルール:
- テキスト中に「（単位：千円）」「単位：千円」「千円」等の記載があれば → "千円"
- テキスト中に「（単位：百万円）」「百万円」等の記載があれば → "百万円"
- テキスト中に「（単位：円）」「単位：円」の記載があれば → "円"
- 記載がない場合、数値の桁数から推測する（7桁以上の数値が多い場合は「円」の可能性が高い）
{{"unit": "千円"}}
【PDFテキスト（先頭部分）】
{pdf_text[:2000]}
JSONのみを返してください。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)
    return result.get("unit", "千円")


def detect_document_types(pdf_text: str, api_key: str = None) -> list:
    """PDFに含まれる財務諸表の種類を検出する（後方互換性のため残す）"""
    return ["balance_sheet", "profit_loss", "manufacturing_cost"]


def parse_balance_sheet(pdf_text: str, api_key: str = None, unit: str = "円") -> dict:
    """貸借対照表をLLMで解析（後方互換性のため残す）"""
    restructured = parse_restructured_data(pdf_text, api_key=api_key, unit=unit)
    return restructured.get("balance_sheet", {})


def parse_profit_loss(pdf_text: str, api_key: str = None, unit: str = "円") -> dict:
    """損益計算書をLLMで解析（後方互換性のため残す）"""
    restructured = parse_restructured_data(pdf_text, api_key=api_key, unit=unit)
    return restructured.get("profit_loss", {})


def parse_manufacturing_cost(pdf_text: str, api_key: str = None, unit: str = "円") -> dict:
    """製造原価報告書をLLMで解析（後方互換性のため残す）"""
    restructured = parse_restructured_data(pdf_text, api_key=api_key, unit=unit)
    return restructured.get("manufacturing_cost", {})


def parse_original_trial_balance(pdf_text: str, api_key: str = None, unit: str = "円") -> dict:
    """試算表の生科目を読み取る（後方互換性のため残す）"""
    meta = parse_original_and_meta(pdf_text, api_key=api_key)
    return {
        "pl_items": meta.get("pl_items", []),
        "bs_items": meta.get("bs_items", []),
        "mcr_items": meta.get("mcr_items", [])
    }
