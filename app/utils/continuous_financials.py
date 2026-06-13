"""
連続F実績・予算 ビルダー

財務諸表組換え（RestructuredPL / RestructuredBS）をもとに、
エクセル「①連続F実績・予算」シート相当の表データを構築する。

提供する表:
  - 連続P/L（過年度実績）          build_continuous_pl
  - 連続B/S（過年度実績）          build_continuous_bs
  - 予算実績P/L（直前期・予実差額） build_budget_actual
  - 連続キャッシュフロー計算書(簡易) build_cashflow

金額はエクセルに合わせて千円単位（円→千円に丸め）で表示する。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


def _v(obj, attr: str) -> int:
    """モデルオブジェクトから整数値（円）を安全に取得する。"""
    if obj is None:
        return 0
    val = getattr(obj, attr, 0)
    try:
        return int(val) if val is not None else 0
    except (TypeError, ValueError):
        return 0


def _sen(yen: Optional[float]) -> Optional[int]:
    """円 → 千円（四捨五入）。None はそのまま。"""
    if yen is None:
        return None
    return int(round(yen / 1000.0))


def fmt_sen(yen: Optional[float]) -> str:
    """円を千円表示（カンマ区切り）に整形する。None/欠損は『－』。"""
    if yen is None:
        return '－'
    s = _sen(yen)
    if s is None:
        return '－'
    if s < 0:
        return f'△{abs(s):,}'
    return f'{s:,}'


def fmt_ratio(value: Optional[float]) -> str:
    """構成比・比率（%）を小数1桁で整形する。None は空欄。"""
    if value is None:
        return ''
    return f'{value:.1f}'


def _ratio(amount: Optional[float], base: Optional[float]) -> Optional[float]:
    """amount ÷ base × 100。base が 0/None なら None。"""
    if amount is None or not base:
        return None
    return amount / base * 100.0


# ============================================================
# 連続P/L（過年度実績）
# ============================================================

# (attr, ラベル, レベル[0=主要/1=内訳], 強調行か)
_PL_LINES = [
    ('sales', '売上高', 0, True),
    ('cost_of_sales', '売上原価', 0, False),
    ('gross_profit', '売上総利益', 0, True),
    ('external_cost_adjustment', '外部経費調整額', 1, False),
    ('gross_added_value', '粗付加価値', 0, True),
    ('selling_general_admin_expenses', '販売費及び一般管理費', 0, False),
    ('labor_cost', '（1）人件費', 1, False),
    ('executive_compensation', '（2）役員報酬', 1, False),
    ('capital_regeneration_cost', '（3）資本再生費', 1, False),
    ('research_development_expenses', '（4）研究開発費', 1, False),
    ('general_expenses', '（5）一般経費', 1, False),
    ('operating_income', '営業利益', 0, True),
    ('financial_profit_loss', '金融損益', 1, False),
    ('other_non_operating', 'その他の営業外損益', 1, False),
    ('ordinary_income', '経常利益', 0, True),
    ('extraordinary_profit_loss', '特別損益', 0, False),
    ('income_before_tax', '税引前当期純利益', 0, True),
    ('income_taxes', '法人税・住民税・事業税', 0, False),
    ('net_income', '当期純利益', 0, True),
    ('dividend', '（1）配当金', 1, False),
    ('retained_profit', '（2）内部留保', 1, False),
]


def build_continuous_pl(periods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """連続P/L（過年度実績）の表データを作る。

    periods: 古い→新しい順。各要素 {'label': str, 'rpl': RestructuredPL|None, ...}
    各セル = {'amount': 表示文字列, 'ratio': 構成比文字列（対売上）}
    """
    labels = [p.get('label', '') for p in periods]
    rows = []
    for attr, label, level, strong in _PL_LINES:
        cells = []
        for p in periods:
            rpl = p.get('rpl')
            if rpl is None:
                cells.append({'amount': '－', 'ratio': ''})
                continue
            amount = _v(rpl, attr)
            sales = _v(rpl, 'sales')
            cells.append({
                'amount': fmt_sen(amount),
                'ratio': fmt_ratio(_ratio(amount, sales)),
            })
        rows.append({'label': label, 'level': level, 'strong': strong, 'cells': cells})
    return {'labels': labels, 'rows': rows}


# ============================================================
# 連続B/S（過年度実績）
# ============================================================

_BS_LINES = [
    ('__head', 'Ⅰ 資産の部', 0, True),
    ('quick_assets', '当座資産', 1, False),
    ('trade_receivables', '売掛債権', 1, False),
    ('inventory_assets', '棚卸資産', 1, False),
    ('other_current_assets', 'その他流動資産', 1, False),
    ('current_assets', '流動資産合計', 1, True),
    ('tangible_fixed_assets', '有形固定資産', 1, False),
    ('intangible_fixed_assets', '無形固定資産', 1, False),
    ('investments_and_other', '投資その他の資産', 1, False),
    ('deferred_assets', '繰延資産', 1, False),
    ('fixed_assets', '固定資産合計', 1, True),
    ('total_assets', '資産合計', 0, True),
    ('__head', 'Ⅱ 負債の部', 0, True),
    ('trade_payables', '買掛債務', 1, False),
    ('short_term_borrowings', '短期借入金', 1, False),
    ('current_portion_long_term', '1年以内返済長期借入金', 1, False),
    ('other_current_liabilities', 'その他流動負債', 1, False),
    ('current_liabilities', '流動負債合計', 1, True),
    ('long_term_borrowings', '長期借入金', 1, False),
    ('executive_borrowings', '役員等借入金', 1, False),
    ('retirement_benefit_liability', '退職給付引当金', 1, False),
    ('other_fixed_liabilities', 'その他固定負債', 1, False),
    ('fixed_liabilities', '固定負債合計', 1, True),
    ('total_liabilities', '負債合計', 0, True),
    ('__head', 'Ⅲ 純資産の部', 0, True),
    ('capital', '資本金', 1, False),
    ('capital_surplus', '資本剰余金', 1, False),
    ('retained_earnings', '利益剰余金', 1, False),
    ('net_assets', '純資産合計', 0, True),
    ('total_liabilities_and_net_assets', '負債・純資産合計', 0, True),
]


def build_continuous_bs(periods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """連続B/S（過年度実績）の表データを作る。構成比は対総資産。"""
    labels = [p.get('label', '') for p in periods]
    rows = []
    for attr, label, level, strong in _BS_LINES:
        if attr == '__head':
            rows.append({'label': label, 'level': level, 'strong': strong,
                         'is_head': True, 'cells': [{'amount': '', 'ratio': ''} for _ in periods]})
            continue
        cells = []
        for p in periods:
            rbs = p.get('rbs')
            if rbs is None:
                cells.append({'amount': '－', 'ratio': ''})
                continue
            amount = _v(rbs, attr)
            total = _v(rbs, 'total_assets')
            cells.append({
                'amount': fmt_sen(amount),
                'ratio': fmt_ratio(_ratio(amount, total)),
            })
        rows.append({'label': label, 'level': level, 'strong': strong,
                     'is_head': False, 'cells': cells})
    return {'labels': labels, 'rows': rows}


# ============================================================
# 予算実績P/L（直前期・予実差額）
# ============================================================

# (実績attr, 予算attr, ラベル, 強調)
_BUDGET_LINES = [
    ('sales', 'budget_sales', '売上高', True),
    ('cost_of_sales', 'budget_cost_of_sales', '売上原価', False),
    ('gross_profit', 'budget_gross_profit', '売上総利益', True),
    ('selling_general_admin_expenses', 'budget_operating_expenses', '販売費及び一般管理費', False),
    ('operating_income', 'budget_operating_income', '営業利益', True),
    ('ordinary_income', 'budget_ordinary_income', '経常利益', True),
    ('income_before_tax', 'budget_income_before_tax', '税引前当期純利益', True),
    ('income_taxes', 'budget_income_tax', '法人税等', False),
    ('net_income', 'budget_net_income', '当期純利益', True),
]


def build_budget_actual(rpl, budget) -> Dict[str, Any]:
    """予算実績P/L（直前期）の表データを作る。

    rpl: RestructuredPL（直前期の実績） / budget: AnnualBudget（無ければ None）
    各行 = 予算 / 実績 / 差額（実績−予算）と達成率。
    """
    rows = []
    for actual_attr, budget_attr, label, strong in _BUDGET_LINES:
        actual = _v(rpl, actual_attr) if rpl is not None else None
        budget_val = None
        if budget is not None:
            raw = getattr(budget, budget_attr, None)
            budget_val = int(raw) if raw is not None else None
        diff = None
        rate = None
        if actual is not None and budget_val is not None:
            diff = actual - budget_val
            rate = _ratio(actual, budget_val)
        rows.append({
            'label': label, 'strong': strong, 'budget_attr': budget_attr,
            'budget_sen': _sen(budget_val) if budget_val is not None else '',
            'budget': fmt_sen(budget_val),
            'actual': fmt_sen(actual),
            'diff': fmt_sen(diff),
            'diff_negative': (diff is not None and diff < 0),
            'rate': fmt_ratio(rate),
        })
    return {'rows': rows, 'has_budget': budget is not None}


# ============================================================
# 連続キャッシュフロー計算書（間接法・簡易）
# ============================================================

_CF_LINES = [
    ('op_pretax', '税引前当期純利益', 0, False),
    ('op_dep', '減価償却費等（資本再生費）', 1, False),
    ('op_receivables', '売掛債権の増減', 1, False),
    ('op_inventory', '棚卸資産の増減', 1, False),
    ('op_payables', '買掛債務の増減', 1, False),
    ('op_tax', '法人税等の支払', 1, False),
    ('op_total', '営業活動によるキャッシュフロー', 0, True),
    ('inv_total', '投資活動によるキャッシュフロー', 0, True),
    ('fin_borrow', '借入金の増減', 1, False),
    ('fin_dividend', '配当金の支払', 1, False),
    ('fin_total', '財務活動によるキャッシュフロー', 0, True),
    ('net_change', '現金及び現金同等物の増減額', 0, True),
    ('beginning_cash', '現金及び現金同等物の期首残高', 0, False),
    ('ending_cash', '現金及び現金同等物の期末残高', 0, True),
]


def _cash(rbs) -> int:
    return _v(rbs, 'cash_on_hand') + _v(rbs, 'investment_deposits')


def _interest_debt(rbs) -> int:
    return (_v(rbs, 'short_term_borrowings') + _v(rbs, 'current_portion_long_term')
            + _v(rbs, 'long_term_borrowings') + _v(rbs, 'executive_borrowings'))


def build_cashflow(periods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """連続キャッシュフロー計算書（間接法・簡易）を作る。

    前期B/Sとの差分が必要なため、前期が存在する期のみ列として出力する。
    """
    columns = []  # (label, values dict)
    for i in range(1, len(periods)):
        cur, prev = periods[i], periods[i - 1]
        rpl, rbs = cur.get('rpl'), cur.get('rbs')
        prev_rbs = prev.get('rbs')
        if rpl is None or rbs is None or prev_rbs is None:
            continue

        pretax = _v(rpl, 'income_before_tax')
        dep = _v(rpl, 'capital_regeneration_cost')
        d_recv = -(_v(rbs, 'trade_receivables') - _v(prev_rbs, 'trade_receivables'))
        d_inv = -(_v(rbs, 'inventory_assets') - _v(prev_rbs, 'inventory_assets'))
        d_pay = (_v(rbs, 'trade_payables') - _v(prev_rbs, 'trade_payables'))
        tax = -_v(rpl, 'income_taxes')
        op_total = pretax + dep + d_recv + d_inv + d_pay + tax

        # 投資CF（簡易）: 固定資産の純増を投資支出とみなす（減価償却を戻し）
        inv_total = -((_v(rbs, 'fixed_assets') - _v(prev_rbs, 'fixed_assets')) + dep)

        fin_borrow = _interest_debt(rbs) - _interest_debt(prev_rbs)
        fin_dividend = -_v(rpl, 'dividend')
        fin_total = fin_borrow + fin_dividend

        net_change = op_total + inv_total + fin_total
        beginning = _cash(prev_rbs)
        ending = beginning + net_change

        columns.append({
            'label': cur.get('label', ''),
            'values': {
                'op_pretax': pretax, 'op_dep': dep, 'op_receivables': d_recv,
                'op_inventory': d_inv, 'op_payables': d_pay, 'op_tax': tax,
                'op_total': op_total, 'inv_total': inv_total,
                'fin_borrow': fin_borrow, 'fin_dividend': fin_dividend,
                'fin_total': fin_total, 'net_change': net_change,
                'beginning_cash': beginning, 'ending_cash': ending,
            },
        })

    labels = [c['label'] for c in columns]
    rows = []
    for key, label, level, strong in _CF_LINES:
        cells = [fmt_sen(c['values'][key]) for c in columns]
        rows.append({'label': label, 'level': level, 'strong': strong, 'cells': cells})
    return {'labels': labels, 'rows': rows, 'has_data': bool(columns)}
