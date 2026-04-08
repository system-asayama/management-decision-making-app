"""
AIマッピング推定サービス

PDFから読み取った勘定科目名を、組換え帳票（RestructuredPL/BS/MCR）の
フィールドに自動マッピングするサービス。
GPT-4.1-miniを使用して科目名から組換え先を推定する。
"""
import json
import os
from openai import OpenAI

client = OpenAI()

# ===== 組換え先フィールド定義 =====

PL_FIELDS = {
    "sales": "1. 売上高",
    "cost_of_sales": "2. 売上原価（合計）",
    "beginning_inventory": "（1）期首棚卸高",
    "manufacturing_cost": "（2）当期製造（工事）原価",
    "ending_inventory": "（3）期末棚卸高",
    "gross_profit": "売上総利益",
    "labor_cost": "（1）人件費",
    "executive_compensation": "（2）役員報酬",
    "capital_regeneration_cost": "（3）資本再生費",
    "research_development_expenses": "（4）研究開発費",
    "general_expenses": "（5）一般経費",
    "general_expenses_fixed": "① 固定費",
    "general_expenses_variable": "② 変動費",
    "selling_general_admin_expenses": "3. 販売費及び一般管理費（合計）",
    "operating_income": "営業利益",
    "financial_profit_loss": "4. 金融損益",
    "other_non_operating": "その他営業外損益",
    "ordinary_income": "経常利益",
    "extraordinary_profit_loss": "5. 特別損益",
    "income_before_tax": "税引前当期純利益",
    "income_taxes": "法人税・住民税・事業税",
    "net_income": "当期純利益",
    "dividend": "（1）配当金",
    "retained_profit": "（2）内部留保",
    "legal_reserve": "① 利益準備金積立額",
    "voluntary_reserve": "② その他剰余金積立額",
    "retained_earnings_increase": "③ 繰越利益剰余金増加",
}

BS_FIELDS = {
    "cash_on_hand": "① 手許現預金",
    "investment_deposits": "② 運用預金",
    "marketable_securities": "③ 有価証券",
    "other_current_assets": "④ その他（流動資産）",
    "trade_receivables": "売掛債権",
    "inventory_assets": "棚卸資産",
    "land": "(1) 土地",
    "buildings_and_attached_facilities": "(2) 建物・附属設備等",
    "machinery_and_equipment": "(3) 機械装置",
    "vehicles_and_transport_equipment": "(4) 車輌運搬具",
    "tools_furniture_and_fixtures": "(5) 工具・器具・備品",
    "other_tangible_fixed_assets": "(6) その他（有形固定資産）",
    "tangible_fixed_assets": "有形固定資産（合計）",
    "intangible_fixed_assets": "無形固定資産",
    "investments_and_other": "投資その他の資産",
    "deferred_assets": "繰延資産",
    "trade_payables": "(1) 買掛債務",
    "short_term_borrowings": "(2) 短期借入金",
    "current_portion_long_term": "長期借入金（1年以内支払い）",
    "discounted_notes": "(3) 割引手形",
    "income_taxes_payable": "(4) 未払法人税等",
    "bonus_reserve": "(5) 賞与引当金",
    "other_allowances": "(6) その他引当金",
    "other_current_liabilities": "(7) その他",
    "long_term_borrowings": "(1) 長期借入金",
    "executive_borrowings": "(2) 役員等借入金",
    "retirement_benefit_liability": "(3) 退職給付引当金",
    "other_fixed_liabilities": "(4) その他",
    "capital": "資本金",
    "capital_reserve": "資本準備金",
    "other_capital_surplus": "その他資本剰余金",
    "capital_surplus": "資本剰余金（合計）",
    "legal_reserve_bs": "利益準備金",
    "voluntary_reserve_bs": "任意積立金",
    "retained_earnings_carried": "繰越利益剰余金",
    "retained_earnings": "利益剰余金（合計）",
    "valuation_and_translation_adjustments": "IV 評価・換算差額等",
    "treasury_stock": "V 自己株式",
    "current_assets": "流動資産合計",
    "fixed_assets": "固定資産合計",
    "total_assets": "資産合計",
    "current_liabilities": "流動負債合計",
    "fixed_liabilities": "固定負債合計",
    "total_liabilities": "負債合計",
    "net_assets": "純資産合計",
    "total_liabilities_and_net_assets": "負債・純資産合計",
}

MCR_FIELDS = {
    "beginning_raw_material": "期首原材料棚卸高",
    "raw_material_purchase": "当期原材料仕入高",
    "ending_raw_material": "期末原材料棚卸高",
    "material_cost": "材料費計",
    "labor_cost_manufacturing": "労務費計",
    "outsourcing_cost": "外注加工費",
    "freight_manufacturing": "荷造運賃（製造）",
    "meeting_cost_manufacturing": "会議費（製造）",
    "travel_cost_manufacturing": "旅費交通費（製造）",
    "communication_cost_manufacturing": "通信費（製造）",
    "supplies_manufacturing": "消耗品費（製造）",
    "vehicle_cost_manufacturing": "車両費（製造）",
    "rent_manufacturing": "賃借料（製造）",
    "insurance_manufacturing": "保険料（製造）",
    "depreciation_manufacturing": "減価償却費（製造）",
    "repair_cost_manufacturing": "修繕費（製造）",
    "other_manufacturing_cost": "その他製造経費",
    "manufacturing_expenses_total": "製造経費計",
    "total_manufacturing_cost_current": "総製造費用",
    "beginning_wip": "期首仕掛品棚卸高",
    "ending_wip": "期末仕掛品棚卸高",
    "total_manufacturing_cost": "製造原価合計",
}


def build_fields_description():
    """AIプロンプト用のフィールド説明文を生成"""
    pl_desc = "\n".join([f"  {k}: {v}" for k, v in PL_FIELDS.items()])
    bs_desc = "\n".join([f"  {k}: {v}" for k, v in BS_FIELDS.items()])
    mcr_desc = "\n".join([f"  {k}: {v}" for k, v in MCR_FIELDS.items()])
    return pl_desc, bs_desc, mcr_desc


def estimate_mappings_for_pl(tenant_id: int, account_items: list) -> list:
    """
    損益計算書科目マスタのAIマッピング推定
    
    Args:
        tenant_id: テナントID
        account_items: PlAccountItemオブジェクトのリスト
    
    Returns:
        マッピング結果のリスト [{id, target_statement, target_field, confidence}, ...]
    """
    unmapped_items = [item for item in account_items if item.mapping_status in ('unmapped', None)]
    if not unmapped_items:
        return []
    
    pl_desc, _, _ = build_fields_description()
    
    account_names = [{"id": item.id, "name": item.account_name} for item in unmapped_items]
    
    prompt = f"""あなたは日本の会計・財務の専門家です。
以下の損益計算書（PL）の勘定科目名を、指定された組換えPLのフィールドにマッピングしてください。

【組換えPLのフィールド一覧】
{pl_desc}

【マッピングルール】
- 各科目を最も適切なフィールドに1対1でマッピングしてください
- 合計行や小計行（「〇〇合計」「〇〇計」など）は target_field を null にしてください
- 明らかに対応するフィールドがない科目は target_field を null にしてください
- 「給料手当」「賞与」「法定福利費」「福利厚生費」などの人件費系は "labor_cost" にマッピング
- 「減価償却費」「修繕費」は "capital_regeneration_cost" にマッピング
- 「受取利息」「受取配当金」は "financial_profit_loss" にマッピング（プラス）
- 「支払利息」は "financial_profit_loss" にマッピング（マイナス）
- 「雑収入」「補助金収入」などは "other_non_operating" にマッピング
- 「固定資産売却益」「固定資産売却損」などは "extraordinary_profit_loss" にマッピング
- confidence は 0.0〜1.0 の信頼度（確信が高いほど1.0に近い）

【マッピング対象科目】
{json.dumps(account_names, ensure_ascii=False)}

以下のJSON形式で回答してください（他のテキストは不要）:
[
  {{"id": 科目ID, "target_statement": "PL", "target_field": "フィールド名またはnull", "confidence": 0.95}},
  ...
]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        # JSONオブジェクト形式で返ってくる場合の対応
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            # {"mappings": [...]} 形式の場合
            for key in parsed:
                if isinstance(parsed[key], list):
                    return parsed[key]
        elif isinstance(parsed, list):
            return parsed
        return []
    except Exception as e:
        print(f"[mapping_service] PL mapping error: {e}")
        return []


def estimate_mappings_for_bs(tenant_id: int, account_items: list) -> list:
    """
    貸借対照表科目マスタのAIマッピング推定
    """
    unmapped_items = [item for item in account_items if item.mapping_status in ('unmapped', None)]
    if not unmapped_items:
        return []
    
    _, bs_desc, _ = build_fields_description()
    
    account_names = [{"id": item.id, "name": item.account_name} for item in unmapped_items]
    
    prompt = f"""あなたは日本の会計・財務の専門家です。
以下の貸借対照表（BS）の勘定科目名を、指定された組換えBSのフィールドにマッピングしてください。

【組換えBSのフィールド一覧】
{bs_desc}

【マッピングルール】
- 各科目を最も適切なフィールドに1対1でマッピングしてください
- 合計行や小計行（「〇〇合計」「〇〇計」など）は target_field を null にしてください
- 銀行口座名（「三井住友〇〇」「みずほ〇〇」など）は "cash_on_hand" にマッピング
- 「売掛金」「受取手形」「未収金」は "trade_receivables" にマッピング
- 「仕掛品」「製品」「商品」「原材料」「貯蔵品」は "inventory_assets" にマッピング
- 「前払費用」「仮払金」「立替金」「未収入金」などの資産科目は "other_current_assets" にマッピング
- 「土地」は "land"、「建物」「建物附属設備」は "buildings_and_attached_facilities" にマッピング
- 「機械装置」は "machinery_and_equipment"、「車両運搬具」は "vehicles_and_transport_equipment" にマッピング
- 「工具器具備品」は "tools_furniture_and_fixtures" にマッピング
- 「買掛金」「支払手形」は "trade_payables" にマッピング
- 「短期借入金」は "short_term_borrowings"、「1年以内返済長期借入金」は "current_portion_long_term" にマッピング
- 「長期借入金」は "long_term_borrowings"、「役員借入金」は "executive_borrowings" にマッピング
- 「未払法人税等」は "income_taxes_payable"、「賞与引当金」は "bonus_reserve" にマッピング
- 「貸倒引当金」などの引当金は "other_allowances" にマッピング
- 「未払金」「未払費用」「預り金」「未払消費税等」は "other_current_liabilities" にマッピング
- クレジットカード名（「ダイナース」「アメックス」等）は "other_current_liabilities" にマッピング
- confidence は 0.0〜1.0 の信頼度

【マッピング対象科目】
{json.dumps(account_names, ensure_ascii=False)}

以下のJSON形式で回答してください（他のテキストは不要）:
[
  {{"id": 科目ID, "target_statement": "BS", "target_field": "フィールド名またはnull", "confidence": 0.95}},
  ...
]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            for key in parsed:
                if isinstance(parsed[key], list):
                    return parsed[key]
        elif isinstance(parsed, list):
            return parsed
        return []
    except Exception as e:
        print(f"[mapping_service] BS mapping error: {e}")
        return []


def estimate_mappings_for_mcr(tenant_id: int, account_items: list) -> list:
    """
    製造原価報告書科目マスタのAIマッピング推定

    MCRの科目は、組換え先としては損益計算書（PL）の項目へ寄せる。
    """
    unmapped_items = [item for item in account_items if item.mapping_status in ('unmapped', None)]
    if not unmapped_items:
        return []
    
    pl_desc, _, _ = build_fields_description()
    
    account_names = [{"id": item.id, "name": item.account_name} for item in unmapped_items]
    
    prompt = f"""あなたは日本の会計・財務の専門家です。
以下の製造原価報告書（MCR）の勘定科目名を、指定された組換えPLのフィールドにマッピングしてください。

【組換えPLのフィールド一覧】
{pl_desc}

【マッピングルール】
- 各科目を最も適切なフィールドに1対1でマッピングしてください
- 合計行や小計行（「〇〇合計」「〇〇計」など）は target_field を null にしてください
- 「期首原材料棚卸高」「期首仕掛品棚卸高」は "beginning_inventory" にマッピング
- 「当期原材料仕入高」「材料費計」「総製造費用」「製造原価合計」は "manufacturing_cost" にマッピング
- 「期末原材料棚卸高」「期末仕掛品棚卸高」は "ending_inventory" にマッピング
- 「労務費計」は "labor_cost" にマッピング
- 「減価償却費」「修繕費」は "capital_regeneration_cost" にマッピング
- その他の製造経費（外注加工費、荷造運賃、旅費交通費、消耗品費など）は原則 "general_expenses" にマッピング
- confidence は 0.0〜1.0 の信頼度

【マッピング対象科目】
{json.dumps(account_names, ensure_ascii=False)}

以下のJSON形式で回答してください（他のテキストは不要）:
[
  {{"id": 科目ID, "target_statement": "PL", "target_field": "フィールド名またはnull", "confidence": 0.95}},
  ...
]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            for key in parsed:
                if isinstance(parsed[key], list):
                    return parsed[key]
        elif isinstance(parsed, list):
            return parsed
        return []
    except Exception as e:
        print(f"[mapping_service] MCR mapping error: {e}")
        return []


def get_all_target_fields():
    """組換え先フィールドの全定義を返す（UI用）"""
    return {
        "PL": PL_FIELDS,
        "BS": BS_FIELDS,
        "MCR": PL_FIELDS,
    }


# ===== 会計システム分類体系 =====

# 大分類・中分類・小分類の階層定義（会計システムと同じ体系）
ACCOUNTING_CATEGORY_TREE = {
    "資産": {
        "流動資産": ["現金及び預金", "売上債権", "棚卸資産", "その他流動資産"],
        "固定資産": ["有形固定資産", "無形固定資産", "投資その他の資産"],
        "繰延資産": ["繰延資産"],
    },
    "負債": {
        "流動負債": ["仕入債務", "その他流動負債"],
        "固定負債": ["固定負債"],
    },
    "純資産": {
        "資本金": ["資本金"],
        "資本剰余金": ["資本剰余金"],
        "利益剰余金": ["利益剰余金"],
        "自己株式": ["自己株式"],
        "評価換算差額等": ["評価換算差額等"],
        "新株予約権": ["新株予約権"],
    },
    "損益": {
        "売上高": ["売上高"],
        "売上原価": ["売上原価"],
        "販売費及び一般管理費": ["販売費", "一般管理費"],
        "営業外収益": ["営業外収益"],
        "営業外費用": ["営業外費用"],
        "特別利益": ["特別利益"],
        "特別損失": ["特別損失"],
        "法人税等": ["法人税等"],
    },
}


def build_category_tree_description():
    """AIプロンプト用の分類体系説明文を生成"""
    lines = []
    for major, mids in ACCOUNTING_CATEGORY_TREE.items():
        lines.append(f"【大分類: {major}】")
        for mid, subs in mids.items():
            sub_str = "、".join(subs)
            lines.append(f"  中分類: {mid} → 小分類: {sub_str}")
    return "\n".join(lines)


def estimate_categories(account_items: list, statement_type: str) -> list:
    """
    勘定科目の大分類・中分類・小分類をAIで推定する

    Args:
        account_items: AccountItemオブジェクトのリスト（category_statusが'uncategorized'または'pending'のもの）
        statement_type: 'PL', 'BS', 'MCR' のいずれか（コンテキスト情報として使用）

    Returns:
        分類結果のリスト [{id, major_category, mid_category, sub_category, confidence}, ...]
    """
    uncategorized_items = [
        item for item in account_items
        if item.category_status in ('uncategorized', None)
    ]
    if not uncategorized_items:
        return []

    category_desc = build_category_tree_description()
    account_names = [{"id": item.id, "name": item.account_name} for item in uncategorized_items]

    prompt = f"""あなたは日本の会計・財務の専門家です。
以下の勘定科目名を、指定された会計分類体系（大分類・中分類・小分類）に分類してください。
この科目は{statement_type}（{'損益計算書' if statement_type == 'PL' else '貸借対照表' if statement_type == 'BS' else '製造原価報告書'}）から読み取られた科目です。

【会計分類体系】
{category_desc}

【分類ルール】
- 各科目を最も適切な大分類・中分類・小分類に分類してください
- 銀行口座名（「三井住友銀行」「みずほ銀行」など）は 大分類:資産、中分類:流動資産、小分類:現金及び預金
- 「売掛金」「受取手形」は 大分類:資産、中分類:流動資産、小分類:売上債権
- 「買掛金」「支払手形」は 大分類:負債、中分類:流動負債、小分類:仕入債務
- 「給料手当」「賞与」「法定福利費」などの人件費は 大分類:損益、中分類:販売費及び一般管理費、小分類:一般管理費
- 製造業の人件費（製造部門）は 大分類:損益、中分類:売上原価、小分類:売上原価
- confidence は 0.0〜1.0 の信頼度（確信が高いほど1.0に近い）

【分類対象科目】
{json.dumps(account_names, ensure_ascii=False)}

以下のJSON形式で回答してください（他のテキストは不要）:
{{
  "results": [
    {{"id": 科目ID, "major_category": "大分類名", "mid_category": "中分類名", "sub_category": "小分類名", "confidence": 0.95}},
    ...
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "results" in parsed:
            return parsed["results"]
        elif isinstance(parsed, list):
            return parsed
        return []
    except Exception as e:
        print(f"[mapping_service] category estimation error: {e}")
        return []
