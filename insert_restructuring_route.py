"""
decision.pyに財務諸表組換え統合ルートを追加し、
既存のpl-restructuringとbs-restructuringをリダイレクトに変更するスクリプト
行番号ベースで処理する
"""

with open('app/blueprints/decision.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# PLルートの開始行（3839行目、0-indexed: 3838）
# BSルートの開始行（3972行目、0-indexed: 3971）
# pl-auto-fillルートの開始行（3940行目、0-indexed: 3939）
# bs-auto-fillルートの開始行（4073行目、0-indexed: 4072）

# PLルートの範囲を特定（3839〜3938行、0-indexed: 3838〜3937）
# BSルートの範囲を特定（3972〜4072行、0-indexed: 3971〜4071）

# 各ルートの開始・終了を行番号で確認
pl_start = None
pl_auto_start = None
bs_start = None
bs_auto_start = None

for i, line in enumerate(lines):
    if "# ==================== PL組換え" in line and pl_start is None:
        pl_start = i
    if "@bp.route('/pl-auto-fill'" in line and pl_auto_start is None:
        pl_auto_start = i
    if "# ==================== BS組換え" in line and bs_start is None:
        bs_start = i
    if "@bp.route('/bs-auto-fill'" in line and bs_auto_start is None:
        bs_auto_start = i

print(f"PL start: {pl_start+1}")
print(f"PL auto-fill start: {pl_auto_start+1}")
print(f"BS start: {bs_start+1}")
print(f"BS auto-fill start: {bs_auto_start+1}")

# PLルート範囲: pl_start 〜 pl_auto_start-1
# BSルート範囲: bs_start 〜 bs_auto_start-1

pl_route_lines = lines[pl_start:pl_auto_start]
bs_route_lines = lines[bs_start:bs_auto_start]

print(f"PL route lines: {len(pl_route_lines)}")
print(f"BS route lines: {len(bs_route_lines)}")

# 統合ルートのコード
new_route = '''# ==================== 財務諸表組換え（統合） ====================
@bp.route('/restructuring', methods=['GET', 'POST'])
@require_roles(ROLES['TENANT_ADMIN'], ROLES['SYSTEM_ADMIN'], ROLES['ADMIN'], ROLES['EMPLOYEE'])
def restructuring():
    """財務諸表組換え（PL・BSをタブで切り替え）"""
    from ..models_decision import RestructuredPL, RestructuredBS
    db = SessionLocal()
    try:
        tenant_id = session.get('tenant_id')
        companies = db.query(Company).filter_by(tenant_id=tenant_id).all()
        company_id = request.args.get('company_id', type=int) or request.form.get('company_id', type=int)
        fiscal_year_id = request.args.get('fiscal_year_id', type=int) or request.form.get('fiscal_year_id', type=int)
        active_tab = request.args.get('tab', 'pl')  # 'pl' or 'bs'
        post_type = request.args.get('type', 'pl')  # POSTの場合はtypeパラメータでPL/BSを判別

        selected_company = None
        fiscal_years = []
        selected_fy = None
        rpl = None
        rbs = None
        otb_pl_items = []
        otb_bs_items = []

        if company_id:
            selected_company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
            if selected_company:
                fiscal_years = db.query(FiscalYear).filter_by(company_id=company_id).order_by(FiscalYear.start_date.desc()).all()

        if fiscal_year_id:
            selected_fy = db.query(FiscalYear).filter_by(id=fiscal_year_id).first()
            if selected_fy:
                rpl = db.query(RestructuredPL).filter_by(fiscal_year_id=fiscal_year_id).first()
                rbs = db.query(RestructuredBS).filter_by(fiscal_year_id=fiscal_year_id).first()
                otb = db.query(OriginalTrialBalance).filter_by(fiscal_year_id=fiscal_year_id).first()
                if otb:
                    import json as json_module
                    if otb.pl_items:
                        try:
                            otb_pl_items = json_module.loads(otb.pl_items)
                            if not isinstance(otb_pl_items, list):
                                otb_pl_items = []
                        except (json_module.JSONDecodeError, ValueError):
                            otb_pl_items = []
                    if otb.bs_items:
                        try:
                            otb_bs_items = json_module.loads(otb.bs_items)
                            if not isinstance(otb_bs_items, list):
                                otb_bs_items = []
                        except (json_module.JSONDecodeError, ValueError):
                            otb_bs_items = []

        if request.method == 'POST':
            if not selected_fy:
                return redirect(url_for('decision.restructuring'))
            def pi(key):
                return parse_int(request.form.get(key, '0') or '0')

            if post_type == 'bs':
                active_tab = 'bs'
                if rbs is None:
                    rbs = RestructuredBS(fiscal_year_id=fiscal_year_id)
                    db.add(rbs)
                rbs.cash_on_hand = pi('cash_on_hand')
                rbs.investment_deposits = pi('investment_deposits')
                rbs.marketable_securities = pi('marketable_securities')
                rbs.trade_receivables = pi('trade_receivables')
                rbs.inventory_assets = pi('inventory_assets')
                rbs.current_assets = pi('current_assets')
                rbs.tangible_fixed_assets = pi('tangible_fixed_assets')
                rbs.intangible_fixed_assets = pi('intangible_fixed_assets')
                rbs.investments_and_other = pi('investments_and_other')
                rbs.deferred_assets = pi('deferred_assets')
                rbs.fixed_assets = pi('fixed_assets')
                rbs.total_assets = pi('total_assets')
                rbs.trade_payables = pi('trade_payables')
                rbs.short_term_borrowings = pi('short_term_borrowings')
                rbs.current_portion_long_term = pi('current_portion_long_term')
                rbs.discounted_notes = pi('discounted_notes')
                rbs.other_current_liabilities = pi('other_current_liabilities')
                rbs.current_liabilities = pi('current_liabilities')
                rbs.long_term_borrowings = pi('long_term_borrowings')
                rbs.executive_borrowings = pi('executive_borrowings')
                rbs.retirement_benefit_liability = pi('retirement_benefit_liability')
                rbs.other_fixed_liabilities = pi('other_fixed_liabilities')
                rbs.fixed_liabilities = pi('fixed_liabilities')
                rbs.total_liabilities = pi('total_liabilities')
                rbs.capital = pi('capital')
                rbs.capital_surplus = pi('capital_surplus')
                rbs.legal_reserve_bs = pi('legal_reserve_bs')
                rbs.voluntary_reserve_bs = pi('voluntary_reserve_bs')
                rbs.retained_earnings_carried = pi('retained_earnings_carried')
                rbs.retained_earnings = pi('retained_earnings')
                rbs.treasury_stock = pi('treasury_stock')
                rbs.net_assets = pi('net_assets')
                rbs.total_liabilities_and_net_assets = pi('total_liabilities_and_net_assets')
                rbs.discounted_notes_note = pi('discounted_notes_note')
                rbs.endorsed_notes_note = pi('endorsed_notes_note')
                db.commit()
                return redirect(url_for('decision.restructuring', company_id=company_id, fiscal_year_id=fiscal_year_id, tab='bs'))
            else:
                if rpl is None:
                    rpl = RestructuredPL(fiscal_year_id=fiscal_year_id)
                    db.add(rpl)
                rpl.sales = pi('sales')
                rpl.beginning_inventory = pi('beginning_inventory')
                rpl.manufacturing_cost = pi('manufacturing_cost')
                rpl.ending_inventory = pi('ending_inventory')
                rpl.cost_of_sales = pi('cost_of_sales')
                rpl.gross_profit = pi('gross_profit')
                rpl.external_cost_adjustment = pi('external_cost_adjustment')
                rpl.gross_added_value = pi('gross_added_value')
                rpl.labor_cost = pi('labor_cost')
                rpl.executive_compensation = pi('executive_compensation')
                rpl.capital_regeneration_cost = pi('capital_regeneration_cost')
                rpl.research_development_expenses = pi('research_development_expenses')
                rpl.general_expenses = pi('general_expenses')
                rpl.general_expenses_fixed = pi('general_expenses_fixed')
                rpl.general_expenses_variable = pi('general_expenses_variable')
                rpl.selling_general_admin_expenses = pi('selling_general_admin_expenses')
                rpl.operating_income = pi('operating_income')
                rpl.financial_profit_loss = pi('financial_profit_loss')
                rpl.other_non_operating = pi('other_non_operating')
                rpl.ordinary_income = pi('ordinary_income')
                rpl.extraordinary_profit_loss = pi('extraordinary_profit_loss')
                rpl.income_before_tax = pi('income_before_tax')
                rpl.income_taxes = pi('income_taxes')
                rpl.net_income = pi('net_income')
                rpl.dividend = pi('dividend')
                rpl.retained_profit = pi('retained_profit')
                rpl.legal_reserve = pi('legal_reserve')
                rpl.voluntary_reserve = pi('voluntary_reserve')
                rpl.retained_earnings_increase = pi('retained_earnings_increase')
                db.commit()
                return redirect(url_for('decision.restructuring', company_id=company_id, fiscal_year_id=fiscal_year_id, tab='pl'))

        return render_template('restructuring.html',
            companies=companies,
            selected_company=selected_company,
            fiscal_years=fiscal_years,
            selected_fy=selected_fy,
            rpl=rpl,
            rbs=rbs,
            otb_pl_items=otb_pl_items,
            otb_bs_items=otb_bs_items,
            active_tab=active_tab,
        )
    except Exception as _e:
        db.rollback()
        _tb = _traceback.format_exc()
        return jsonify({'error': str(_e), 'traceback': _tb}), 500
    finally:
        db.close()

'''

# PLリダイレクトルート
pl_redirect = '''# ==================== PL組換え（後方互換リダイレクト） ====================
@bp.route('/pl-restructuring', methods=['GET', 'POST'])
@require_roles(ROLES['TENANT_ADMIN'], ROLES['SYSTEM_ADMIN'], ROLES['ADMIN'], ROLES['EMPLOYEE'])
def pl_restructuring():
    """後方互換: /restructuring?tab=pl にリダイレクト"""
    company_id = request.args.get('company_id')
    fiscal_year_id = request.args.get('fiscal_year_id')
    kwargs = {'tab': 'pl'}
    if company_id:
        kwargs['company_id'] = company_id
    if fiscal_year_id:
        kwargs['fiscal_year_id'] = fiscal_year_id
    return redirect(url_for('decision.restructuring', **kwargs))

'''

# BSリダイレクトルート
bs_redirect = '''# ==================== BS組換え（後方互換リダイレクト） ====================
@bp.route('/bs-restructuring', methods=['GET', 'POST'])
@require_roles(ROLES['TENANT_ADMIN'], ROLES['SYSTEM_ADMIN'], ROLES['ADMIN'], ROLES['EMPLOYEE'])
def bs_restructuring():
    """後方互換: /restructuring?tab=bs にリダイレクト"""
    company_id = request.args.get('company_id')
    fiscal_year_id = request.args.get('fiscal_year_id')
    kwargs = {'tab': 'bs'}
    if company_id:
        kwargs['company_id'] = company_id
    if fiscal_year_id:
        kwargs['fiscal_year_id'] = fiscal_year_id
    return redirect(url_for('decision.restructuring', **kwargs))

'''

# 新しいlines配列を構築
# 順序: [0..pl_start-1] + new_route + pl_redirect + [pl_auto_start..bs_start-1] + bs_redirect + [bs_auto_start..]
new_lines = (
    lines[:pl_start] +
    [new_route] +
    [pl_redirect] +
    lines[pl_auto_start:bs_start] +
    [bs_redirect] +
    lines[bs_auto_start:]
)

with open('app/blueprints/decision.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"decision.py updated: {len(new_lines)}行")

# 確認
with open('app/blueprints/decision.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
routes = re.findall(r"@bp\.route\('(/[^']+)'", content)
restructuring_routes = [r for r in routes if 'restructuring' in r or 'auto-fill' in r]
print("Restructuring routes:", restructuring_routes)
