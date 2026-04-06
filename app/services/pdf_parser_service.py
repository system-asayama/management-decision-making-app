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


def detect_unit(pdf_text: str, api_key: str = None) -> str:
    """PDFの金額単位を検出する（円 / 千円 / 百万円）"""
    client = get_openai_client(api_key)
    prompt = f"""以下の財務諸表PDFテキストの金額単位を判定してください。

判定ルール:
- テキスト中に「（単位：千円）」「単位：千円」「千円」等の記載があれば → "千円"
- テキスト中に「（単位：百万円）」「百万円」等の記載があれば → "百万円"
- テキスト中に「（単位：円）」「単位：円」の記載があれば → "円"
- 記載がない場合、数値の桁数から推測する（7桁以上の数値が多い場合は「円」の可能性が高い）

【出力フォーマット（JSON）】
{{"unit": "千円"}}  // "円" または "千円" または "百万円" のいずれか

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


def parse_balance_sheet(pdf_text: str, api_key: str = None, unit: str = "千円") -> dict:
    """貸借対照表をLLMで解析してフィールドマッピングを返す"""
    client = get_openai_client(api_key)

    unit_instruction = {
        "円": "- 金額は「円」単位で記載されています。1000で割って千円単位の整数に変換して返す（例: 1,234,000円 → 1234）",
        "千円": "- 金額は「千円」単位で記載されています。そのまま整数で返す（例: 1,234千円 → 1234）",
        "百万円": "- 金額は「百万円」単位で記載されています。1000を掛けて千円単位の整数に変換して返す（例: 1,234百万円 → 1234000）",
    }.get(unit, "- 金額はそのまま整数で返す")

    prompt = f"""以下は財務諸表PDFから抽出したテキストです。
このテキストから「貸借対照表（Balance Sheet）」の数値を読み取り、
指定されたJSONフォーマットで返してください。

【重要なルール】
{unit_instruction}
- 該当する項目が見つからない場合は 0 を返す
- カンマや円マークは除去して純粋な整数を返す
- 数値が見つからない場合は必ず 0 を返す（nullや文字列は不可）

【出力フォーマット（JSON）】
{{
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
}}

【PDFテキスト】
{pdf_text[:8000]}

JSONのみを返してください。説明文は不要です。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    # 全フィールドを整数に変換
    return {k: int(v) if v else 0 for k, v in result.items()}


def parse_profit_loss(pdf_text: str, api_key: str = None, unit: str = "千円") -> dict:
    """損益計算書をLLMで解析してフィールドマッピングを返す"""
    client = get_openai_client(api_key)

    unit_instruction = {
        "円": "- 金額は「円」単位で記載されています。1000で割って千円単位の整数に変換して返す（例: 1,234,000円 → 1234）",
        "千円": "- 金額は「千円」単位で記載されています。そのまま整数で返す（例: 1,234千円 → 1234）",
        "百万円": "- 金額は「百万円」単位で記載されています。1000を掛けて千円単位の整数に変換して返す（例: 1,234百万円 → 1234000）",
    }.get(unit, "- 金額はそのまま整数で返す")

    prompt = f"""以下は財務諸表PDFから抽出したテキストです。
このテキストから「損益計算書（Profit and Loss Statement）」の数値を読み取り、
指定されたJSONフォーマットで返してください。

【重要なルール】
{unit_instruction}
- 該当する項目が見つからない場合は 0 を返す
- カンマや円マークは除去して純粋な整数を返す
- 費用項目は正の整数で返す（マイナスにしない）
- 損益（プラスマイナス）がある場合は符号付きで返す

【出力フォーマット（JSON）】
{{
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
}}

【PDFテキスト】
{pdf_text[:8000]}

JSONのみを返してください。説明文は不要です。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return {k: int(v) if v else 0 for k, v in result.items()}


def parse_manufacturing_cost(pdf_text: str, api_key: str = None, unit: str = "千円") -> dict:
    """製造原価報告書をLLMで解析してフィールドマッピングを返す"""
    client = get_openai_client(api_key)

    unit_instruction = {
        "円": "- 金額は「円」単位で記載されています。1000で割って千円単位の整数に変換して返す（例: 1,234,000円 → 1234）",
        "千円": "- 金額は「千円」単位で記載されています。そのまま整数で返す（例: 1,234千円 → 1234）",
        "百万円": "- 金額は「百万円」単位で記載されています。1000を掛けて千円単位の整数に変換して返す（例: 1,234百万円 → 1234000）",
    }.get(unit, "- 金額はそのまま整数で返す")

    prompt = f"""以下は財務諸表PDFから抽出したテキストです。
このテキストから「製造原価報告書（Cost of Manufacturing Report）」の数値を読み取り、
指定されたJSONフォーマットで返してください。

【重要なルール】
{unit_instruction}
- 該当する項目が見つからない場合は 0 を返す
- カンマや円マークは除去して純粋な整数を返す

【出力フォーマット（JSON）】
{{
  "material_cost": <材料費>,
  "labor_cost_manufacturing": <労務費（製造）>,
  "outsourcing_cost": <外注費>,
  "depreciation_manufacturing": <減価償却費（製造）>,
  "repair_cost_manufacturing": <修繕費（製造）>,
  "other_manufacturing_cost": <その他製造経費>,
  "total_manufacturing_cost_current": <当期総製造費用>,
  "beginning_wip": <期首仕掛品棚卸高>,
  "ending_wip": <期末仕掛品棚卸高>,
  "total_manufacturing_cost": <当期製造原価合計>
}}

【PDFテキスト】
{pdf_text[:8000]}

JSONのみを返してください。説明文は不要です。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return {k: int(v) if v else 0 for k, v in result.items()}


def detect_document_types(pdf_text: str, api_key: str = None) -> list:
    """PDFに含まれる財務諸表の種類を検出する"""
    client = get_openai_client(api_key)
    prompt = f"""以下のPDFテキストに含まれる財務諸表の種類を判定してください。

含まれている可能性のある財務諸表:
- balance_sheet: 貸借対照表
- profit_loss: 損益計算書
- manufacturing_cost: 製造原価報告書

【出力フォーマット（JSON）】
{{
  "types": ["balance_sheet", "profit_loss", "manufacturing_cost"]
  // 含まれているものだけリストに含める
}}

【PDFテキスト（先頭部分）】
{pdf_text[:3000]}

JSONのみを返してください。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("types", [])


def parse_financial_pdf(pdf_path: str, target_types: list = None, api_key: str = None) -> dict:
    """
    PDFを解析して財務諸表データを返す

    Args:
        pdf_path: PDFファイルのパス
        target_types: 解析対象の種類リスト（None の場合は自動検出）
                      例: ["balance_sheet", "profit_loss", "manufacturing_cost"]

    Returns:
        {
            "detected_types": [...],
            "unit": "千円",
            "balance_sheet": {...} or None,
            "profit_loss": {...} or None,
            "manufacturing_cost": {...} or None,
            "raw_text": "..."
        }
    """
    # テキスト抽出
    pdf_text = extract_text_from_pdf(pdf_path)

    if not pdf_text.strip():
        return {
            "error": "PDFからテキストを抽出できませんでした。スキャンされたPDFの場合はOCRが必要です。",
            "detected_types": [],
            "unit": "千円",
            "balance_sheet": None,
            "profit_loss": None,
            "manufacturing_cost": None,
            "raw_text": ""
        }

    # 金額単位を先に検出
    try:
        unit = detect_unit(pdf_text, api_key=api_key)
    except Exception:
        unit = "千円"  # デフォルトは千円

    # 財務諸表の種類を検出
    if target_types is None:
        detected_types = detect_document_types(pdf_text, api_key=api_key)
    else:
        detected_types = target_types

    result = {
        "detected_types": detected_types,
        "unit": unit,
        "balance_sheet": None,
        "profit_loss": None,
        "manufacturing_cost": None,
        "raw_text": pdf_text[:2000]  # プレビュー用
    }

    # 各財務諸表を解析（検出した単位を渡す）
    if "balance_sheet" in detected_types:
        try:
            result["balance_sheet"] = parse_balance_sheet(pdf_text, api_key=api_key, unit=unit)
        except Exception as e:
            result["balance_sheet_error"] = str(e)

    if "profit_loss" in detected_types:
        try:
            result["profit_loss"] = parse_profit_loss(pdf_text, api_key=api_key, unit=unit)
        except Exception as e:
            result["profit_loss_error"] = str(e)

    if "manufacturing_cost" in detected_types:
        try:
            result["manufacturing_cost"] = parse_manufacturing_cost(pdf_text, api_key=api_key, unit=unit)
        except Exception as e:
            result["manufacturing_cost_error"] = str(e)

    return result
