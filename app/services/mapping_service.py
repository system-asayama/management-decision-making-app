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
    "sales": "売上高",
    "cost_of_sales": "売上原価（合計）",
    "beginning_inventory": "期首棚卸高",
    "manufacturing_cost": "当期製造（工事）原価",
    "ending_inventory": "期末棚卸高",
    "gross_profit": "売上総利益",
    "labor_cost": "人件費",
    "executive_compensation": "役員報酬",
    "capital_regeneration_cost": "資本再生費（減価償却費＋修繕費）",
    "research_development_expenses": "研究開発費",
    "general_expenses": "一般経費",
    "general_expenses_fixed": "一般経費（固定費）",
    "general_expenses_variable": "一般経費（変動費）",
    "selling_general_admin_expenses": "販売費及び一般管理費（合計）",
    "operating_income": "営業利益",
    "financial_profit_loss": "金融損益（受取利息－支払利息）",
    "other_non_operating": "その他営業外損益",
    "ordinary_income": "経常利益",
    "extraordinary_profit_loss": "特別損益",
    "income_before_tax": "税引前当期純利益",
    "income_taxes": "法人税等",
    "net_income": "当期純利益",
    "dividend": "配当金",
    "retained_profit": "内部留保",
    "legal_reserve": "利益準備金積立額",
    "voluntary_reserve": "その他剰余金積立額",
    "retained_earnings_increase": "繰越利益剰余金増加",
}

BS_FIELDS = {
    "cash_on_hand": "手許現預金",
    "investment_deposits": "運用預金",
    "marketable_securities": "有価証券",
    "trade_receivables": "売掛債権（売掛金＋受取手形）",
    "inventory_assets": "棚卸資産",
    "current_assets": "流動資産合計",
    "tangible_fixed_assets": "有形固定資産",
    "intangible_fixed_assets": "無形固定資産",
    "investments_and_other": "投資その他の資産",
    "deferred_assets": "繰延資産",
    "fixed_assets": "固定資産合計",
    "total_assets": "資産合計",
    "trade_payables": "買掛債務",
    "short_term_borrowings": "短期借入金",
    "current_portion_long_term": "1年以内返済の長期借入金",
    "discounted_notes": "割引手形",
    "other_current_liabilities": "その他流動負債",
    "current_liabilities": "流動負債合計",
    "long_term_borrowings": "長期借入金",
    "executive_borrowings": "役員等借入金",
    "retirement_benefit_liability": "退職給付引当金",
    "other_fixed_liabilities": "その他固定負債",
    "fixed_liabilities": "固定負債合計",
    "total_liabilities": "負債合計",
    "capital": "資本金",
    "capital_surplus": "資本剰余金",
    "retained_earnings": "利益剰余金合計",
    "legal_reserve_bs": "利益準備金",
    "voluntary_reserve_bs": "任意積立金",
    "retained_earnings_carried": "繰越利益剰余金",
    "treasury_stock": "自己株式",
    "net_assets": "純資産合計",
    "total_liabilities_and_net_assets": "負債純資産合計",
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


def estimate_mappings_for_pl(company_id: int, account_items: list) -> list:
    """
    損益計算書科目マスタのAIマッピング推定
    
    Args:
        company_id: 企業ID
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


def estimate_mappings_for_bs(company_id: int, account_items: list) -> list:
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
- 「売掛金」「受取手形」は "trade_receivables" にマッピング
- 「仕掛品」「製品」「商品」「原材料」は "inventory_assets" にマッピング
- 「前払費用」「仮払金」「立替金」「未収入金」などは "other_current_liabilities" の資産側として適切なフィールドを選択
- 「買掛金」「支払手形」は "trade_payables" にマッピング
- 「未払金」「未払費用」「預り金」「未払法人税等」「未払消費税等」は "other_current_liabilities" にマッピング
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


def estimate_mappings_for_mcr(company_id: int, account_items: list) -> list:
    """
    製造原価報告書科目マスタのAIマッピング推定
    """
    unmapped_items = [item for item in account_items if item.mapping_status in ('unmapped', None)]
    if not unmapped_items:
        return []
    
    _, _, mcr_desc = build_fields_description()
    
    account_names = [{"id": item.id, "name": item.account_name} for item in unmapped_items]
    
    prompt = f"""あなたは日本の会計・財務の専門家です。
以下の製造原価報告書（MCR）の勘定科目名を、指定された組換えMCRのフィールドにマッピングしてください。

【組換えMCRのフィールド一覧】
{mcr_desc}

【マッピングルール】
- 各科目を最も適切なフィールドに1対1でマッピングしてください
- 合計行や小計行（「〇〇合計」「〇〇計」など）は target_field を null にしてください
- 「外注費」「外注加工費」は "outsourcing_cost" にマッピング
- 製造系の経費（「（製造）」が付くもの）は対応するフィールドにマッピング
- confidence は 0.0〜1.0 の信頼度

【マッピング対象科目】
{json.dumps(account_names, ensure_ascii=False)}

以下のJSON形式で回答してください（他のテキストは不要）:
[
  {{"id": 科目ID, "target_statement": "MCR", "target_field": "フィールド名またはnull", "confidence": 0.95}},
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
        "MCR": MCR_FIELDS,
    }
