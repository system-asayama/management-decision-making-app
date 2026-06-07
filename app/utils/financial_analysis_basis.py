"""
財務分析基礎データ

財務諸表組換え（RestructuredPL / RestructuredBS）の数値をもとに、
成長力・収益力・資金力・生産力の4視点の経営分析指標を計算する。

エクセル「経営分析指標」シートを参考に、計算式・単位・目標値・評価記号
（◎○△×）・採否を付与して返す。

金額系のモデル値は「1円単位」で保持されているため、
千円単位で表示する指標は 1000 で除して算出する。
"""
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 小さなヘルパー
# ---------------------------------------------------------------------------
def _num(obj: Any, attr: str) -> float:
    """モデルの属性を float で安全に取得（None / 欠損は 0）。"""
    if obj is None:
        return 0.0
    value = getattr(obj, attr, 0)
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _safe_div(numerator: float, denominator: float) -> Optional[float]:
    """ゼロ除算を避けた除算。分母が 0 の場合は None。"""
    if not denominator:
        return None
    return numerator / denominator


# ---------------------------------------------------------------------------
# 評価記号（◎○△×）
# ---------------------------------------------------------------------------
def _grade_higher_better(value: Optional[float], target: float) -> str:
    """値が大きいほど良い指標の評価。"""
    if value is None:
        return ''
    if value >= target * 1.2:
        return '◎'
    if value >= target:
        return '○'
    if value >= target * 0.8:
        return '△'
    return '×'


def _grade_lower_better(value: Optional[float], target: float) -> str:
    """値が小さいほど良い指標の評価。"""
    if value is None:
        return ''
    if target <= 0:
        return ''
    if value <= target * 0.8:
        return '◎'
    if value <= target:
        return '○'
    if value <= target * 1.2:
        return '△'
    return '×'


def _grade_growth(value: Optional[float], base: float = 100.0) -> str:
    """成長率（指数）の評価。base=100 が前年同水準。"""
    if value is None:
        return ''
    if value >= base + 10:
        return '◎'
    if value >= base:
        return '○'
    if value >= base - 10:
        return '△'
    return '×'


def _grade_vs_sales(value: Optional[float], sales_index: Optional[float],
                    higher_better: bool) -> str:
    """売上高成長率(①)との比較で評価する成長指標。"""
    if value is None or sales_index is None:
        return ''
    diff = value - sales_index
    if not higher_better:
        diff = -diff
    if diff >= 5:
        return '◎'
    if diff >= 0:
        return '○'
    if diff >= -10:
        return '△'
    return '×'


# ---------------------------------------------------------------------------
# 表示用フォーマット
# ---------------------------------------------------------------------------
def _fmt(value: Optional[float], unit: str) -> str:
    """指標値を単位に応じて表示用文字列へ整形する。"""
    if value is None:
        return ''
    if unit == '千円':
        return f'{value:,.0f}'
    if unit == '回':
        return f'{value:.1f}'
    # %・月 などは小数1桁
    return f'{value:.1f}'


# ---------------------------------------------------------------------------
# 1期分の基礎数値を抽出
# ---------------------------------------------------------------------------
def _extract(rpl: Any, rbs: Any, employee_count: float) -> Dict[str, float]:
    """RestructuredPL / RestructuredBS から計算に必要な基礎数値を取り出す。"""
    # ---- PL ----
    sales = _num(rpl, 'sales')
    cost_of_sales = _num(rpl, 'cost_of_sales')
    gross_profit = _num(rpl, 'gross_profit') or (sales - cost_of_sales)
    gross_added_value = _num(rpl, 'gross_added_value')
    labor_cost = _num(rpl, 'labor_cost')
    executive_compensation = _num(rpl, 'executive_compensation')
    capital_regeneration_cost = _num(rpl, 'capital_regeneration_cost')
    research_development_expenses = _num(rpl, 'research_development_expenses')
    general_expenses = _num(rpl, 'general_expenses')
    general_expenses_variable = _num(rpl, 'general_expenses_variable')
    operating_income = _num(rpl, 'operating_income')
    financial_profit_loss = _num(rpl, 'financial_profit_loss')  # 受取利息－支払利息
    ordinary_income = _num(rpl, 'ordinary_income')
    income_before_tax = _num(rpl, 'income_before_tax')
    purchases = _num(rpl, 'current_purchases') or cost_of_sales

    # ---- BS ----
    cash_on_hand = _num(rbs, 'cash_on_hand')
    investment_deposits = _num(rbs, 'investment_deposits')
    marketable_securities = _num(rbs, 'marketable_securities')
    trade_receivables = _num(rbs, 'trade_receivables')
    inventory_assets = _num(rbs, 'inventory_assets')
    current_assets = _num(rbs, 'current_assets')
    land = _num(rbs, 'land')
    tangible_fixed_assets = _num(rbs, 'tangible_fixed_assets')
    investments_and_other = _num(rbs, 'investments_and_other')
    deferred_assets = _num(rbs, 'deferred_assets')
    fixed_assets = _num(rbs, 'fixed_assets')
    total_assets = _num(rbs, 'total_assets')
    trade_payables = _num(rbs, 'trade_payables')
    short_term_borrowings = _num(rbs, 'short_term_borrowings')
    current_portion_long_term = _num(rbs, 'current_portion_long_term')
    discounted_notes = _num(rbs, 'discounted_notes')
    bonus_reserve = _num(rbs, 'bonus_reserve')
    other_allowances = _num(rbs, 'other_allowances')
    other_current_liabilities = _num(rbs, 'other_current_liabilities')
    current_liabilities = _num(rbs, 'current_liabilities')
    long_term_borrowings = _num(rbs, 'long_term_borrowings')
    executive_borrowings = _num(rbs, 'executive_borrowings')
    retirement_benefit_liability = _num(rbs, 'retirement_benefit_liability')
    fixed_liabilities = _num(rbs, 'fixed_liabilities')
    total_liabilities = _num(rbs, 'total_liabilities')
    net_assets = _num(rbs, 'net_assets')

    # ---- 派生値 ----
    cash_deposits = cash_on_hand + investment_deposits
    quick_assets = cash_deposits + marketable_securities + trade_receivables
    interest_bearing_debt = (short_term_borrowings + current_portion_long_term
                             + discounted_notes + long_term_borrowings
                             + executive_borrowings)
    allowances = bonus_reserve + other_allowances + retirement_benefit_liability
    operating_capital = total_assets - investments_and_other - deferred_assets
    if operating_capital <= 0:
        operating_capital = total_assets
    other_added_value = (gross_added_value - labor_cost - executive_compensation
                         - capital_regeneration_cost
                         - research_development_expenses - general_expenses)
    variable_cost = cost_of_sales + general_expenses_variable
    marginal_profit = sales - variable_cost
    total_personnel = labor_cost + executive_compensation
    credit_funding = trade_payables + other_current_liabilities + fixed_liabilities
    collateral_capacity = (land + marketable_securities) * 0.5 - interest_bearing_debt
    emp = employee_count if employee_count and employee_count > 0 else 0

    return {
        'sales': sales,
        'cost_of_sales': cost_of_sales,
        'gross_profit': gross_profit,
        'gross_added_value': gross_added_value,
        'labor_cost': labor_cost,
        'executive_compensation': executive_compensation,
        'capital_regeneration_cost': capital_regeneration_cost,
        'research_development_expenses': research_development_expenses,
        'general_expenses': general_expenses,
        'operating_income': operating_income,
        'financial_profit_loss': financial_profit_loss,
        'ordinary_income': ordinary_income,
        'income_before_tax': income_before_tax,
        'purchases': purchases,
        'cash_deposits': cash_deposits,
        'quick_assets': quick_assets,
        'trade_receivables': trade_receivables,
        'inventory_assets': inventory_assets,
        'current_assets': current_assets,
        'tangible_fixed_assets': tangible_fixed_assets,
        'fixed_assets': fixed_assets,
        'total_assets': total_assets,
        'trade_payables': trade_payables,
        'current_liabilities': current_liabilities,
        'fixed_liabilities': fixed_liabilities,
        'total_liabilities': total_liabilities,
        'net_assets': net_assets,
        'interest_bearing_debt': interest_bearing_debt,
        'allowances': allowances,
        'operating_capital': operating_capital,
        'other_added_value': other_added_value,
        'marginal_profit': marginal_profit,
        'total_personnel': total_personnel,
        'credit_funding': credit_funding,
        'collateral_capacity': collateral_capacity,
        'employee_count': emp,
        'has_data': bool(rpl or rbs),
    }


# ---------------------------------------------------------------------------
# 各視点の指標を計算（1期分の値リストを返す）
# ---------------------------------------------------------------------------
def _profitability_values(d: Dict[str, float]) -> Dict[str, Optional[float]]:
    sales = d['sales']
    return {
        'roa': _pct(_safe_div(d['ordinary_income'], d['total_assets'])),
        'ordinary_to_sales': _pct(_safe_div(d['ordinary_income'], sales)),
        'total_capital_turnover': _safe_div(sales, d['total_assets']),
        'roe': _pct(_safe_div(d['ordinary_income'], d['net_assets'])),
        'equity_turnover': _safe_div(sales, d['net_assets']),
        'operating_capital_return': _pct(_safe_div(d['operating_income'], d['operating_capital'])),
        'operating_to_sales': _pct(_safe_div(d['operating_income'], sales)),
        'operating_capital_turnover': _safe_div(sales, d['operating_capital']),
        'gross_margin': _pct(_safe_div(d['gross_profit'], sales)),
        'added_value_to_sales': _pct(_safe_div(d['gross_added_value'], sales)),
        'labor_to_sales': _pct(_safe_div(d['labor_cost'], sales)),
        'executive_to_sales': _pct(_safe_div(d['executive_compensation'], sales)),
        'capital_regen_to_sales': _pct(_safe_div(d['capital_regeneration_cost'], sales)),
        'rd_to_sales': _pct(_safe_div(d['research_development_expenses'], sales)),
        'general_to_sales': _pct(_safe_div(d['general_expenses'], sales)),
        'other_added_to_sales': _pct(_safe_div(d['other_added_value'], sales)),
        'marginal_ratio': _pct(_safe_div(d['marginal_profit'], sales)),
        'cost_ratio': _pct(_safe_div(d['cost_of_sales'], sales)),
    }


def _financial_strength_values(d: Dict[str, float]) -> Dict[str, Optional[float]]:
    sales = d['sales']
    cl = d['current_liabilities']
    monthly_sales = _safe_div(sales, 12)
    monthly_purchases = _safe_div(d['purchases'], 12)
    return {
        'equity_ratio': _pct(_safe_div(d['net_assets'], d['total_assets'])),
        'financial_funding_ratio': _pct(_safe_div(d['interest_bearing_debt'], d['total_assets'])),
        'allowance_funding_ratio': _pct(_safe_div(d['allowances'], d['total_assets'])),
        'credit_funding_ratio': _pct(_safe_div(d['credit_funding'], d['total_assets'])),
        'borrowing_dependency': _pct(_safe_div(d['interest_bearing_debt'], sales)),
        'collateral_capacity': _safe_div(d['collateral_capacity'], 1000),  # 千円
        'financial_burden_ratio': _pct(_safe_div(-d['financial_profit_loss'], d['gross_profit'])),
        'cash_turnover_months': _safe_div(d['cash_deposits'], monthly_sales) if monthly_sales else None,
        'receivables_turnover': _safe_div(sales, d['trade_receivables']),
        'receivables_months': _safe_div(d['trade_receivables'], monthly_sales) if monthly_sales else None,
        'payables_turnover': _safe_div(d['purchases'], d['trade_payables']),
        'payables_months': _safe_div(d['trade_payables'], monthly_purchases) if monthly_purchases else None,
        'inventory_turnover': _safe_div(sales, d['inventory_assets']),
        'inventory_months': _safe_div(d['inventory_assets'], monthly_sales) if monthly_sales else None,
        'current_ratio': _pct(_safe_div(d['current_assets'], cl)),
        'quick_ratio': _pct(_safe_div(d['quick_assets'], cl)),
        'cash_ratio': _pct(_safe_div(d['cash_deposits'], cl)),
        'long_term_fit_ratio': _pct(_safe_div(d['fixed_assets'], d['net_assets'] + d['fixed_liabilities'])),
    }


def _productivity_values(d: Dict[str, float]) -> Dict[str, Optional[float]]:
    sales = d['sales']
    emp = d['employee_count']
    equipment = d['tangible_fixed_assets']
    return {
        'added_value_to_capital': _pct(_safe_div(d['gross_added_value'], d['total_assets'])),
        'added_value_to_sales': _pct(_safe_div(d['gross_added_value'], sales)),
        'total_capital_turnover': _safe_div(sales, d['total_assets']),
        'labor_productivity': _safe_div(d['gross_added_value'] / 1000, emp) if emp else None,
        'sales_per_employee': _safe_div(sales / 1000, emp) if emp else None,
        'profit_per_employee': _safe_div(d['income_before_tax'] / 1000, emp) if emp else None,
        'labor_distribution': _pct(_safe_div(d['total_personnel'], d['gross_added_value'])),
        'equipment_efficiency': _pct(_safe_div(d['gross_added_value'], equipment)),
        'equipment_per_employee': _safe_div(equipment / 1000, emp) if emp else None,
    }


def _pct(value: Optional[float]) -> Optional[float]:
    """比率を百分率（％）へ。"""
    if value is None:
        return None
    return value * 100


# ---------------------------------------------------------------------------
# 指標定義（番号・名称・計算式・単位・目標値・評価方法）
# ---------------------------------------------------------------------------
# 各タプル: (key, no, name, formula, unit, target_text, grade_fn, is_main, adopted)
#   grade_fn(value) -> 記号文字列。None で評価なし。

def _build_rows(defs, period_value_dicts):
    """指標定義と各期の値辞書から、テンプレート描画用の行リストを作る。"""
    rows = []
    for d in defs:
        key, no, name, formula, unit, target, grade_fn, is_main, adopted = d
        cells = []
        for vd in period_value_dicts:
            if vd is None:
                cells.append({'display': '', 'grade': ''})
                continue
            value = vd.get(key)
            grade = grade_fn(value) if grade_fn else ''
            cells.append({'display': _fmt(value, unit), 'grade': grade})
        rows.append({
            'no': no, 'name': name, 'formula': formula, 'unit': unit,
            'target': target, 'cells': cells, 'is_main': is_main,
            'adopted': adopted,
        })
    return rows


def _profitability_defs():
    g_ge = lambda t: (lambda v: _grade_higher_better(v, t))
    return [
        ('roa', '①', '総資本経常利益率', '経常利益÷総資本', '%', '≧5', g_ge(5), True, True),
        ('ordinary_to_sales', 'a', '売上高経常利益率', '経常利益÷売上高', '%', '', None, False, False),
        ('total_capital_turnover', 'b', '総資本回転率', '売上高÷総資本', '回', '', None, False, False),
        ('roe', '②', '自己資本経常利益率', '経常利益÷自己資本', '%', '≧20', g_ge(20), True, True),
        ('ordinary_to_sales', 'a', '売上高経常利益率', '①の(a)', '%', '', None, False, False),
        ('equity_turnover', 'b', '自己資本回転率', '売上高÷自己資本', '回', '', None, False, False),
        ('operating_capital_return', '③', '経営資本営業利益率', '営業利益÷経営資本', '%', '≧7', g_ge(7), True, True),
        ('operating_to_sales', 'a', '売上高営業利益率', '営業利益÷売上高', '%', '', None, False, False),
        ('operating_capital_turnover', 'b', '経営資本回転率', '売上高÷経営資本', '回', '', None, False, False),
        ('gross_margin', '④', '売上高総利益率', '売上総利益÷売上高', '%', '業界標準', None, True, True),
        ('added_value_to_sales', '⑤', '売上高付加価値率', '付加価値÷売上高', '%', '業界標準', None, True, True),
        ('labor_to_sales', 'a', '売上高人件費率', '人件費÷売上高', '%', '', None, False, False),
        ('executive_to_sales', 'b', '売上高役員報酬費率', '役員報酬÷売上高', '%', '', None, False, False),
        ('capital_regen_to_sales', 'c', '売上高資本再生費率', '資本再生費÷売上高', '%', '', None, False, False),
        ('rd_to_sales', 'd', '売上高研究開発費率', '研究開発費÷売上高', '%', '', None, False, False),
        ('general_to_sales', 'e', '売上高一般経費率', '一般経費÷売上高', '%', '', None, False, False),
        ('other_added_to_sales', 'f', '売上高その他付加価値率', 'その他付加価値÷売上高', '%', '', None, False, False),
        ('marginal_ratio', '⑥', '限界利益率', '限界利益÷売上高', '%', '業界標準', None, True, True),
        ('cost_ratio', '⑦', '売上高売上原価率', '売上原価÷売上高', '%', '業界標準', None, True, True),
    ]


def _financial_strength_defs():
    g_ge = lambda t: (lambda v: _grade_higher_better(v, t))
    g_le = lambda t: (lambda v: _grade_lower_better(v, t))
    return [
        ('equity_ratio', '①', '自己調達率（自己資本比率）', '自己資本÷総資本', '%', '＞30', g_ge(30), True, True),
        ('financial_funding_ratio', '②', '金融調達率', '有利子負債÷総資本', '%', '≦30', g_le(30), True, True),
        ('allowance_funding_ratio', '③', '引当調達率', '各種引当金÷総資本', '%', '', None, True, False),
        ('credit_funding_ratio', '④', '信用調達率', '買掛債務・その他流動負債・固定負債÷総資本', '%', '＜50', g_le(50), True, True),
        ('borrowing_dependency', '⑤', '借入金依存率', '借入金・割引手形÷年間売上高', '%', '≦20', g_le(20), True, True),
        ('collateral_capacity', '⑥', '担保余力', '〔土地・有価証券×50％〕－有利子負債', '千円', '大きい程良', None, True, True),
        ('financial_burden_ratio', '⑦', '金融負担率', '〔支払利息－受取利息〕÷売上総利益', '%', '≦4', g_le(4), True, True),
        ('cash_turnover_months', '⑧', '現預金回転期間', '期末現預金÷（売上高÷12ヶ月）', '月', '', None, True, False),
        ('receivables_turnover', '⑨', '売掛債権回転率', '売上高÷期末売掛債権', '回', '', None, True, False),
        ('receivables_months', '⑩', '売掛債権回転期間', '期末売掛債権÷（売上高÷12ヶ月）', '月', '＜1.5', g_le(1.5), True, True),
        ('payables_turnover', '⑪', '買掛債務回転率', '仕入高÷期末買掛債務', '回', '', None, True, False),
        ('payables_months', '⑫', '買掛債務回転期間', '期末買掛債務÷（仕入高÷12ヶ月）', '月', '＞1.7', g_ge(1.7), True, True),
        ('inventory_turnover', '⑬', '棚卸資産回転率', '売上高÷期末棚卸資産', '回', '', None, True, False),
        ('inventory_months', '⑭', '棚卸資産回転期間', '期末棚卸資産÷（売上高÷12ヶ月）', '月', '＜1', g_le(1), True, True),
        ('current_ratio', '⑮', '流動比率', '流動資産÷流動負債', '%', '≧150', g_ge(150), True, True),
        ('quick_ratio', '⑯', '当座比率', '当座資産÷流動負債', '%', '≧100', g_ge(100), True, True),
        ('cash_ratio', '⑰', '現預金比率', '現預金÷流動負債', '%', '≧20', g_ge(20), True, True),
        ('long_term_fit_ratio', '⑱', '長期適合率', '固定資産÷（自己資本＋固定負債）', '%', '≦90', g_le(90), True, True),
    ]


def _productivity_defs():
    g_ge = lambda t: (lambda v: _grade_higher_better(v, t))
    g_le = lambda t: (lambda v: _grade_lower_better(v, t))
    return [
        ('added_value_to_capital', '①', '総資本付加価値率', '粗付加価値÷総資本', '%', '≧50', g_ge(50), True, True),
        ('added_value_to_sales', 'a', '売上高付加価値率', '粗付加価値÷売上高', '%', '', None, False, False),
        ('total_capital_turnover', 'b', '総資本回転率', '売上高÷総資本', '回', '', None, False, False),
        ('labor_productivity', '②', '付加価値労働生産性', '粗付加価値÷平均従業員数', '千円', '≧7,200', g_ge(7200), True, True),
        ('added_value_to_sales', 'a', '売上高付加価値率', '粗付加価値÷売上高', '%', '', None, False, False),
        ('sales_per_employee', 'b', '従業員一人当り売上高', '売上高÷平均従業員数', '千円', '', None, False, False),
        ('profit_per_employee', '③', '利益生産性', '税引前当期純利益÷平均従業員数', '千円', '≧700', g_ge(700), True, True),
        ('labor_distribution', '④', '労働分配率', '総人件費÷粗付加価値', '%', '≦65', g_le(65), True, True),
        ('equipment_efficiency', '⑤', '設備投資効率', '粗付加価値÷平均設備残高', '%', '≧100', g_ge(100), True, True),
        ('equipment_per_employee', '⑥', '労働装備高', '平均設備残高÷平均従業員数', '千円', '', None, False, False),
    ]


# 成長力の指標定義: (key, no, name, target_text, target_type, is_main, adopted)
#   target_type: 'gt100'（>100）, 'gt_sales'（>①）, 'lt_sales'（<①）, None
_GROWTH_DEFS = [
    ('sales', '①', '売上高成長率', '当年売上高÷前年売上高', '＞100', 'gt100', True, True),
    ('cost_of_sales', '②', '売上原価成長率', '当年売上原価÷前年売上原価', '＜①', 'lt_sales', True, False),
    ('gross_added_value', '③', '付加価値成長率', '当年付加価値÷前年付加価値', '＞①', 'gt_sales', True, True),
    ('labor_cost', 'a', '人件費成長率', '当年人件費÷前年人件費', '', None, False, False),
    ('executive_compensation', 'b', '役員報酬成長率', '当年役員報酬÷前年役員報酬', '', None, False, False),
    ('capital_regeneration_cost', 'c', '資本再生費成長率', '当年資本再生費÷前年資本再生費', '', None, False, False),
    ('research_development_expenses', 'd', '研究開発費成長率', '当年研究開発費÷前年研究開発費', '', None, False, False),
    ('general_expenses', 'e', '一般経費成長率', '当年一般経費÷前年一般経費', '', None, False, True),
    ('fixed_assets', '④', '固定資産成長率', '当年固定資産÷前年固定資産', '＜①', 'lt_sales', True, False),
    ('total_liabilities', '⑤', '他人資本成長率', '当年他人資本÷前年他人資本', '＜①', 'lt_sales', True, False),
    ('income_before_tax', '⑥', '税引前利益成長率', '当年税引前利益÷前年税引前利益', '＞①', 'gt_sales', True, True),
    ('net_assets', '⑦', '自己資本成長率', '当年自己資本÷前年自己資本', '＞①', 'gt_sales', True, True),
]


def _build_growth_rows(period_bases: List[Optional[Dict[str, float]]]):
    """成長力の行を作る。各期の値は『当期÷前期×100』の指数。

    period_bases は古い順（3年前→直前期）の基礎数値辞書のリスト。
    成長率は前期が存在する列のみ算出する（先頭列は空欄）。
    """
    n = len(period_bases)
    # 先に各期の売上高成長指数を計算（>①/<①判定用）
    sales_index = [None] * n
    for i in range(1, n):
        cur, prev = period_bases[i], period_bases[i - 1]
        if cur and prev:
            sales_index[i] = _safe_index(cur.get('sales'), prev.get('sales'))

    rows = []
    for key, no, name, formula, target, ttype, is_main, adopted in _GROWTH_DEFS:
        cells = [{'display': '', 'grade': ''}]  # 先頭列（最古期）は前期なし
        for i in range(1, n):
            cur, prev = period_bases[i], period_bases[i - 1]
            value = None
            if cur and prev:
                value = _safe_index(cur.get(key), prev.get(key))
            grade = ''
            if value is not None:
                if ttype == 'gt100':
                    grade = _grade_growth(value, 100)
                elif ttype == 'gt_sales':
                    grade = _grade_vs_sales(value, sales_index[i], higher_better=True)
                elif ttype == 'lt_sales':
                    grade = _grade_vs_sales(value, sales_index[i], higher_better=False)
            cells.append({'display': _fmt(value, '%') if value is not None else '', 'grade': grade})
        rows.append({
            'no': no, 'name': name, 'formula': formula, 'unit': '%',
            'target': target, 'cells': cells, 'is_main': is_main,
            'adopted': adopted,
        })
    return rows


def _safe_index(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """成長指数 = 当期 ÷ 前期 × 100。前期が 0 / None なら None。"""
    if not previous:
        return None
    if current is None:
        return None
    return current / previous * 100


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------
def build_analysis_basis(periods: List[Dict[str, Any]],
                         employee_count: Optional[int]) -> Dict[str, Any]:
    """財務分析基礎データを構築する。

    Args:
        periods: 古い順（3年前→直前期）の期データ。
                 各要素 = {'label': str, 'rpl': RestructuredPL|None,
                            'rbs': RestructuredBS|None}
        employee_count: 平均従業員数（生産力計算用）

    Returns:
        テンプレート描画用の dict。
        {
          'labels': [...],                 # 期ラベル
          'growth': [行...],
          'profitability': [行...],
          'financial_strength': [行...],
          'productivity': [行...],
          'has_any_data': bool,
        }
    """
    emp = float(employee_count) if employee_count else 0.0

    labels = [p.get('label', '') for p in periods]
    bases: List[Optional[Dict[str, float]]] = []
    for p in periods:
        if p.get('rpl') is None and p.get('rbs') is None:
            bases.append(None)
        else:
            bases.append(_extract(p.get('rpl'), p.get('rbs'), emp))

    profit_vals = [(_profitability_values(b) if b else None) for b in bases]
    strength_vals = [(_financial_strength_values(b) if b else None) for b in bases]
    productivity_vals = [(_productivity_values(b) if b else None) for b in bases]

    return {
        'labels': labels,
        'growth': _build_growth_rows(bases),
        'profitability': _build_rows(_profitability_defs(), profit_vals),
        'financial_strength': _build_rows(_financial_strength_defs(), strength_vals),
        'productivity': _build_rows(_productivity_defs(), productivity_vals),
        'has_any_data': any(b is not None for b in bases),
    }
