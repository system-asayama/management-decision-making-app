"""
経営意思決定アプリ - メインBlueprint
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from ..utils.decorators import require_roles, ROLES
from ..utils.formatting import parse_int, parse_int_or_none
from ..db import SessionLocal
from ..models_decision import Company, FiscalYear, ProfitLossStatement, BalanceSheet, RestructuredPL, RestructuredBS, ManufacturingCostReport, OriginalTrialBalance, RawProfitLossStatement, RawBalanceSheet, RawManufacturingCostReport, AccountMapping, StatementType, PlAccountItem, PlStatementValue, BsAccountItem, BsStatementValue, McrAccountItem, McrStatementValue
from datetime import datetime

bp = Blueprint('decision', __name__, url_prefix='/decision')


@bp.route('/')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def index():
    """経営意思決定アプリのトップページ"""
    tenant_id = session.get('tenant_id')
    
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    return redirect(url_for('decision.company_list'))


@bp.route('/dashboard')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def dashboard():
    """経営意思決定ダッシュボード"""
    tenant_id = session.get('tenant_id')
    
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    return render_template('decision_dashboard.html', tenant_id=tenant_id)


# ============================================================
# 企業管理ルート
# ============================================================

@bp.route('/companies')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def company_list():
    """企業一覧ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('company_list.html', companies=companies)
    finally:
        db.close()


@bp.route('/companies/new', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def company_new():
    """企業登録ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    if request.method == 'POST':
        db = SessionLocal()
        try:
            company = Company(
                tenant_id=tenant_id,
                name=request.form.get('name'),
                industry=request.form.get('industry') or None,
                capital=parse_int_or_none(request.form.get('capital')),
                employee_count=parse_int_or_none(request.form.get('employee_count')),
                established_date=datetime.strptime(request.form.get('established_date'), '%Y-%m-%d').date() if request.form.get('established_date') else None,
                address=request.form.get('address') or None,
                phone=request.form.get('phone') or None,
                email=request.form.get('email') or None,
                website=request.form.get('website') or None,
                notes=request.form.get('notes') or None
            )
            db.add(company)
            db.commit()
            return redirect(url_for('decision.company_list'))
        except Exception as e:
            db.rollback()
            return render_template('company_form.html', error=str(e))
        finally:
            db.close()
    
    return render_template('company_form.html')


@bp.route('/companies/<int:company_id>/edit', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def company_edit(company_id):
    """企業編集ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return redirect(url_for('decision.company_list'))
        
        if request.method == 'POST':
            try:
                company.name = request.form.get('name')
                company.industry = request.form.get('industry') or None
                company.capital = parse_int_or_none(request.form.get('capital'))
                company.employee_count = parse_int_or_none(request.form.get('employee_count'))
                company.established_date = datetime.strptime(request.form.get('established_date'), '%Y-%m-%d').date() if request.form.get('established_date') else None
                company.address = request.form.get('address') or None
                company.phone = request.form.get('phone') or None
                company.email = request.form.get('email') or None
                company.website = request.form.get('website') or None
                company.notes = request.form.get('notes') or None
                db.commit()
                return redirect(url_for('decision.company_list'))
            except Exception as e:
                db.rollback()
                return render_template('company_form.html', company=company, error=str(e))
        
        return render_template('company_form.html', company=company)
    finally:
        db.close()


@bp.route('/companies/<int:company_id>', methods=['GET', 'DELETE'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def company_detail_or_delete(company_id):
    """企業詳細ページ (GET) / 企業削除API (DELETE)"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        if request.method == 'DELETE':
            return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
        return redirect(url_for('decision.index'))

    db = SessionLocal()
    try:
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()

        if not company:
            if request.method == 'DELETE':
                return jsonify({'success': False, 'error': '企業が見つかりません'}), 404
            return redirect(url_for('decision.company_list'))

        if request.method == 'DELETE':
            try:
                db.delete(company)
                db.commit()
                return jsonify({'success': True})
            except Exception as e:
                db.rollback()
                return jsonify({'success': False, 'error': str(e)}), 500

        fiscal_years = db.query(FiscalYear).filter(
            FiscalYear.company_id == company_id
        ).order_by(FiscalYear.start_date.desc()).all()

        return render_template('company_detail.html', company=company, fiscal_years=fiscal_years)
    finally:
        db.close()


# ============================================================
# 企業別カテゴリページ（会計年度・財務データ・経営分析）
# ============================================================

@bp.route('/companies/<int:company_id>/fiscal-years')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def company_fiscal_years(company_id):
    """企業別 会計年度管理ページ"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
        if not company:
            return redirect(url_for('decision.company_list'))
        fiscal_years = db.query(FiscalYear).filter_by(company_id=company_id).order_by(FiscalYear.start_date.desc()).all()
        return render_template('company_fiscal_years.html', company=company, fiscal_years=fiscal_years)
    finally:
        db.close()


@bp.route('/companies/<int:company_id>/financial-data')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def company_financial_data(company_id):
    """企業別 財務データページ"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
        if not company:
            return redirect(url_for('decision.company_list'))
        return render_template('company_financial_data.html', company=company)
    finally:
        db.close()


@bp.route('/companies/<int:company_id>/financial-statements')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def company_financial_statements(company_id):
    """企業別 読み取り済み財務諸表表示ページ"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
        if not company:
            return redirect(url_for('decision.company_list'))

        fiscal_years = db.query(FiscalYear).filter_by(company_id=company_id).order_by(FiscalYear.start_date.desc()).all()

        fiscal_year_data = []
        for fy in fiscal_years:
            # 新テーブル（PlStatementValue / BsStatementValue / McrStatementValue）から読み込む
            pl_values = (
                db.query(PlStatementValue, PlAccountItem)
                  .join(PlAccountItem, PlStatementValue.account_item_id == PlAccountItem.id)
                  .filter(PlStatementValue.fiscal_year_id == fy.id)
                  .order_by(PlAccountItem.display_order)
                  .all()
            )
            bs_values = (
                db.query(BsStatementValue, BsAccountItem)
                  .join(BsAccountItem, BsStatementValue.account_item_id == BsAccountItem.id)
                  .filter(BsStatementValue.fiscal_year_id == fy.id)
                  .order_by(BsAccountItem.display_order)
                  .all()
            )
            mcr_values = (
                db.query(McrStatementValue, McrAccountItem)
                  .join(McrAccountItem, McrStatementValue.account_item_id == McrAccountItem.id)
                  .filter(McrStatementValue.fiscal_year_id == fy.id)
                  .order_by(McrAccountItem.display_order)
                  .all()
            )
            # セクション別表示用ヘルパー関数
            def build_section_view(items_src):
                """[{name, amount, section?}] または [(StatementValue, AccountItem)] から
                セクション別表示データ {section: [{name, amount}]} を構築する"""
                import collections
                section_data = collections.OrderedDict()  # {section: [{name, amount}]}
                no_section = []  # sectionなし科目
                if not items_src:
                    return section_data, no_section
                if isinstance(items_src[0], dict):
                    # JSON形式（OriginalTrialBalance由来）
                    for item in items_src:
                        sec = item.get('section', '')
                        entry = {'name': item.get('name', ''), 'amount': item.get('amount', 0)}
                        if sec:
                            if sec not in section_data:
                                section_data[sec] = []
                            section_data[sec].append(entry)
                        else:
                            no_section.append(entry)
                else:
                    # (StatementValue, AccountItem) タプル形式
                    for sv, ai in items_src:
                        # mid_categoryをsectionとして使用
                        sec = getattr(ai, 'mid_category', None) or ''
                        entry = {'name': ai.account_name, 'amount': sv.amount}
                        if sec:
                            if sec not in section_data:
                                section_data[sec] = []
                            section_data[sec].append(entry)
                        else:
                            no_section.append(entry)
                return section_data, no_section

            # テンプレート向けに {'name': ..., 'amount': ...} 形式に変換（フラットリスト）
            pl_items  = [{'name': ai.account_name, 'amount': sv.amount} for sv, ai in pl_values]
            bs_items  = [{'name': ai.account_name, 'amount': sv.amount} for sv, ai in bs_values]
            mcr_items = [{'name': ai.account_name, 'amount': sv.amount} for sv, ai in mcr_values]

            # セクション別表示データを作成
            bs_section_data, bs_no_section   = build_section_view(bs_values)
            pl_section_data, pl_no_section   = build_section_view(pl_values)
            mcr_section_data, mcr_no_section = build_section_view(mcr_values)

            # OriginalTrialBalanceからsectionフィールドを取得
            import json as json_module
            otb = db.query(OriginalTrialBalance).filter_by(fiscal_year_id=fy.id).first()
            otb_unit = '円'
            if otb:
                otb_unit = getattr(otb, 'unit', '円') or '円'

            def _safe_json_loads(s):
                if not s:
                    return []
                try:
                    result = json_module.loads(s)
                    return result if isinstance(result, list) else []
                except (json_module.JSONDecodeError, ValueError):
                    return []

            # 旧データ（OriginalTrialBalance）からのフォールバック（新テーブルにデータがない場合）
            if not (pl_items or bs_items or mcr_items):
                if otb:
                    pl_items  = _safe_json_loads(otb.pl_items)
                    bs_items  = _safe_json_loads(otb.bs_items)
                    mcr_items = _safe_json_loads(otb.mcr_items)
                    # OriginalTrialBalanceのJSONからセクション別データを再構築
                    bs_section_data, bs_no_section   = build_section_view(bs_items)
                    pl_section_data, pl_no_section   = build_section_view(pl_items)
                    mcr_section_data, mcr_no_section = build_section_view(mcr_items)
            else:
                # 新テーブルにデータがある場合でも、OriginalTrialBalanceのsectionを優先使用
                if otb:
                    otb_bs = _safe_json_loads(otb.bs_items)
                    otb_pl = _safe_json_loads(otb.pl_items)
                    otb_mcr = _safe_json_loads(otb.mcr_items)
                    if otb_bs and any(i.get('section') for i in otb_bs):
                        bs_section_data, bs_no_section = build_section_view(otb_bs)
                    if otb_pl and any(i.get('section') for i in otb_pl):
                        pl_section_data, pl_no_section = build_section_view(otb_pl)
                    if otb_mcr and any(i.get('section') for i in otb_mcr):
                        mcr_section_data, mcr_no_section = build_section_view(otb_mcr)

            unit = otb_unit
            if pl_items or bs_items or mcr_items:
                fiscal_year_data.append({
                    'fiscal_year': fy,
                    'pl_items': pl_items,
                    'bs_items': bs_items,
                    'mcr_items': mcr_items,
                    'bs_section_data': bs_section_data,
                    'bs_no_section': bs_no_section,
                    'pl_section_data': pl_section_data,
                    'pl_no_section': pl_no_section,
                    'mcr_section_data': mcr_section_data,
                    'mcr_no_section': mcr_no_section,
                    'unit': unit,
                    'has_data': True
                })

        return render_template('financial_statements_view.html',
                               company=company,
                               fiscal_year_data=fiscal_year_data)
    finally:
        db.close()


@bp.route('/companies/<int:company_id>/analysis')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def company_analysis(company_id):
    """企業別 経営分析ページ"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
        if not company:
            return redirect(url_for('decision.company_list'))
        return render_template('company_analysis.html', company=company)
    finally:
        db.close()


# ============================================================
# 会計年度管理ルート
# ============================================================

@bp.route('/fiscal-years')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def fiscal_year_list():
    """会計年度一覧ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        fiscal_years = db.query(FiscalYear).join(Company).filter(
            Company.tenant_id == tenant_id
        ).all()
        return render_template('fiscal_year_list.html', fiscal_years=fiscal_years)
    finally:
        db.close()


@bp.route('/fiscal-years/new', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def fiscal_year_new():
    """会計年度登録ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        
        if request.method == 'POST':
            try:
                fiscal_year = FiscalYear(
                    company_id=int(request.form.get('company_id')),
                    year_name=request.form.get('year_name'),
                    start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                    end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
                    months=parse_int(request.form.get('months'), default=12),
                    notes=request.form.get('notes') or None
                )
                db.add(fiscal_year)
                db.commit()
                # 企業別会計年度ページにリダイレクト
                cid = fiscal_year.company_id
                return redirect(url_for('decision.company_fiscal_years', company_id=cid))
            except Exception as e:
                db.rollback()
                preselect_company_id = request.form.get('company_id')
                return render_template('fiscal_year_form.html', companies=companies, error=str(e), preselect_company_id=preselect_company_id)
        
        # GETパラメータからcompany_idを受け取る
        preselect_company_id = request.args.get('company_id')
        return render_template('fiscal_year_form.html', companies=companies, preselect_company_id=preselect_company_id)
    finally:
        db.close()


@bp.route('/fiscal-years/<int:fiscal_year_id>/edit', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def fiscal_year_edit(fiscal_year_id):
    """会計年度編集ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        fiscal_year = db.query(FiscalYear).join(Company).filter(
            FiscalYear.id == fiscal_year_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not fiscal_year:
            return redirect(url_for('decision.fiscal_year_list'))
        
        if request.method == 'POST':
            try:
                fiscal_year.company_id = int(request.form.get('company_id'))
                fiscal_year.year_name = request.form.get('year_name')
                fiscal_year.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
                fiscal_year.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
                fiscal_year.months = parse_int(request.form.get('months'), default=12)
                fiscal_year.notes = request.form.get('notes') or None
                db.commit()
                return redirect(url_for('decision.company_fiscal_years', company_id=fiscal_year.company_id))
            except Exception as e:
                db.rollback()
                return render_template('fiscal_year_form.html', companies=companies, fiscal_year=fiscal_year, error=str(e))
        
        return render_template('fiscal_year_form.html', companies=companies, fiscal_year=fiscal_year)
    finally:
        db.close()


@bp.route('/fiscal-years/<int:fiscal_year_id>', methods=['DELETE'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def fiscal_year_delete(fiscal_year_id):
    """会計年度削除API"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    db = SessionLocal()
    try:
        fiscal_year = db.query(FiscalYear).join(Company).filter(
            FiscalYear.id == fiscal_year_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'success': False, 'error': '会計年度が見つかりません'}), 404
        
        db.delete(fiscal_year)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== 損益計算書管理 ====================

@bp.route('/profit-loss')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def profit_loss_list():
    """損益計算書一覧ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement
        profit_loss_statements = db.query(ProfitLossStatement).join(FiscalYear).join(Company).filter(
            Company.tenant_id == tenant_id
        ).all()
        return render_template('profit_loss_list.html', profit_loss_statements=profit_loss_statements)
    finally:
        db.close()


@bp.route('/profit-loss/new', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"])
def profit_loss_new():
    """損益計算書新規登録ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement
        
        # 会計年度一覧を取得
        fiscal_years = db.query(FiscalYear).join(Company).filter(
            Company.tenant_id == tenant_id
        ).all()
        
        if request.method == 'POST':
            try:
                profit_loss = ProfitLossStatement(
                    fiscal_year_id=int(request.form.get('fiscal_year_id')),
                    sales=parse_int(request.form.get('sales'), default=0),
                    cost_of_sales=parse_int(request.form.get('cost_of_sales'), default=0),
                    gross_profit=parse_int(request.form.get('gross_profit'), default=0),
                    operating_expenses=parse_int(request.form.get('operating_expenses'), default=0),
                    operating_income=parse_int(request.form.get('operating_income'), default=0),
                    non_operating_income=parse_int(request.form.get('non_operating_income'), default=0),
                    non_operating_expenses=parse_int(request.form.get('non_operating_expenses'), default=0),
                    ordinary_income=parse_int(request.form.get('ordinary_income'), default=0),
                    extraordinary_income=parse_int(request.form.get('extraordinary_income'), default=0),
                    extraordinary_loss=parse_int(request.form.get('extraordinary_loss'), default=0),
                    income_before_tax=parse_int(request.form.get('income_before_tax'), default=0),
                    income_tax=parse_int(request.form.get('income_tax'), default=0),
                    net_income=parse_int(request.form.get('net_income'), default=0)
                )
                db.add(profit_loss)
                db.commit()
                return redirect(url_for('decision.profit_loss_list'))
            except Exception as e:
                db.rollback()
                return render_template('profit_loss_form.html', fiscal_years=fiscal_years, error=str(e))
        
        return render_template('profit_loss_form.html', fiscal_years=fiscal_years, profit_loss=None)
    finally:
        db.close()


@bp.route('/profit-loss/<int:id>/edit', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"])
def profit_loss_edit(id):
    """損益計算書編集ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement
        
        # 会計年度一覧を取得
        fiscal_years = db.query(FiscalYear).join(Company).filter(
            Company.tenant_id == tenant_id
        ).all()
        
        # 損益計算書を取得
        profit_loss = db.query(ProfitLossStatement).join(FiscalYear).join(Company).filter(
            ProfitLossStatement.id == id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not profit_loss:
            return redirect(url_for('decision.profit_loss_list'))
        
        if request.method == 'POST':
            try:
                profit_loss.fiscal_year_id = int(request.form.get('fiscal_year_id'))
                profit_loss.sales = parse_int(request.form.get('sales'), default=0)
                profit_loss.cost_of_sales = parse_int(request.form.get('cost_of_sales'), default=0)
                profit_loss.gross_profit = parse_int(request.form.get('gross_profit'), default=0)
                profit_loss.operating_expenses = parse_int(request.form.get('operating_expenses'), default=0)
                profit_loss.operating_income = parse_int(request.form.get('operating_income'), default=0)
                profit_loss.non_operating_income = parse_int(request.form.get('non_operating_income'), default=0)
                profit_loss.non_operating_expenses = parse_int(request.form.get('non_operating_expenses'), default=0)
                profit_loss.ordinary_income = parse_int(request.form.get('ordinary_income'), default=0)
                profit_loss.extraordinary_income = parse_int(request.form.get('extraordinary_income'), default=0)
                profit_loss.extraordinary_loss = parse_int(request.form.get('extraordinary_loss'), default=0)
                profit_loss.income_before_tax = parse_int(request.form.get('income_before_tax'), default=0)
                profit_loss.income_tax = parse_int(request.form.get('income_tax'), default=0)
                profit_loss.net_income = parse_int(request.form.get('net_income'), default=0)
                db.commit()
                return redirect(url_for('decision.profit_loss_list'))
            except Exception as e:
                db.rollback()
                return render_template('profit_loss_form.html', fiscal_years=fiscal_years, profit_loss=profit_loss, error=str(e))
        
        return render_template('profit_loss_form.html', fiscal_years=fiscal_years, profit_loss=profit_loss)
    finally:
        db.close()


@bp.route('/profit-loss/<int:id>', methods=['DELETE'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"])
def profit_loss_delete(id):
    """損益計算書削除API"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement
        
        profit_loss = db.query(ProfitLossStatement).join(FiscalYear).join(Company).filter(
            ProfitLossStatement.id == id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not profit_loss:
            return jsonify({'success': False, 'error': '損益計算書が見つかりません'}), 404
        
        db.delete(profit_loss)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== 貸借対照表管理 ====================

@bp.route('/balance-sheets')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def balance_sheet_list():
    """貸借対照表一覧ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    db = SessionLocal()
    try:
        from app.models_decision import BalanceSheet
        balance_sheets = db.query(BalanceSheet).join(FiscalYear).join(Company).filter(
            Company.tenant_id == tenant_id
        ).all()
        return render_template('balance_sheet_list.html', balance_sheets=balance_sheets)
    finally:
        db.close()


@bp.route('/balance-sheets/new', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"])
def balance_sheet_new():
    """貸借対照表新規登録ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    db = SessionLocal()
    try:
        from app.models_decision import BalanceSheet
        
        # 会計年度一覧を取得
        fiscal_years = db.query(FiscalYear).join(Company).filter(
            Company.tenant_id == tenant_id
        ).all()
        
        if request.method == 'POST':
            try:
                balance_sheet = BalanceSheet(
                    fiscal_year_id=int(request.form.get('fiscal_year_id')),
                    current_assets=parse_int(request.form.get('current_assets'), default=0),
                    fixed_assets=parse_int(request.form.get('fixed_assets'), default=0),
                    total_assets=parse_int(request.form.get('total_assets'), default=0),
                    current_liabilities=parse_int(request.form.get('current_liabilities'), default=0),
                    fixed_liabilities=parse_int(request.form.get('fixed_liabilities'), default=0),
                    total_liabilities=parse_int(request.form.get('total_liabilities'), default=0),
                    capital=parse_int(request.form.get('capital'), default=0),
                    retained_earnings=parse_int(request.form.get('retained_earnings'), default=0),
                    total_equity=parse_int(request.form.get('total_equity'), default=0)
                )
                db.add(balance_sheet)
                db.commit()
                return redirect(url_for('decision.balance_sheet_list'))
            except Exception as e:
                db.rollback()
                return render_template('balance_sheet_form.html', fiscal_years=fiscal_years, error=str(e))
        
        return render_template('balance_sheet_form.html', fiscal_years=fiscal_years, balance_sheet=None)
    finally:
        db.close()


@bp.route('/balance-sheets/<int:id>/edit', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"])
def balance_sheet_edit(id):
    """貸借対照表編集ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    db = SessionLocal()
    try:
        from app.models_decision import BalanceSheet
        
        # 会計年度一覧を取得
        fiscal_years = db.query(FiscalYear).join(Company).filter(
            Company.tenant_id == tenant_id
        ).all()
        
        # 貸借対照表を取得
        balance_sheet = db.query(BalanceSheet).join(FiscalYear).join(Company).filter(
            BalanceSheet.id == id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not balance_sheet:
            return redirect(url_for('decision.balance_sheet_list'))
        
        if request.method == 'POST':
            try:
                balance_sheet.fiscal_year_id = int(request.form.get('fiscal_year_id'))
                balance_sheet.current_assets = parse_int(request.form.get('current_assets'), default=0)
                balance_sheet.fixed_assets = parse_int(request.form.get('fixed_assets'), default=0)
                balance_sheet.total_assets = parse_int(request.form.get('total_assets'), default=0)
                balance_sheet.current_liabilities = parse_int(request.form.get('current_liabilities'), default=0)
                balance_sheet.fixed_liabilities = parse_int(request.form.get('fixed_liabilities'), default=0)
                balance_sheet.total_liabilities = parse_int(request.form.get('total_liabilities'), default=0)
                balance_sheet.capital = parse_int(request.form.get('capital'), default=0)
                balance_sheet.retained_earnings = parse_int(request.form.get('retained_earnings'), default=0)
                balance_sheet.total_equity = parse_int(request.form.get('total_equity'), default=0)
                db.commit()
                return redirect(url_for('decision.balance_sheet_list'))
            except Exception as e:
                db.rollback()
                return render_template('balance_sheet_form.html', fiscal_years=fiscal_years, balance_sheet=balance_sheet, error=str(e))
        
        return render_template('balance_sheet_form.html', fiscal_years=fiscal_years, balance_sheet=balance_sheet)
    finally:
        db.close()


@bp.route('/balance-sheets/<int:id>', methods=['DELETE'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"])
def balance_sheet_delete(id):
    """貸借対照表削除API"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    db = SessionLocal()
    try:
        from app.models_decision import BalanceSheet
        
        balance_sheet = db.query(BalanceSheet).join(FiscalYear).join(Company).filter(
            BalanceSheet.id == id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not balance_sheet:
            return jsonify({'success': False, 'error': '貸借対照表が見つかりません'}), 404
        
        db.delete(balance_sheet)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== ダッシュボード ====================

@bp.route('/dashboard-analysis')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def dashboard_analysis():
    """ダッシュボード分析ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return render_template('decision_no_tenant.html')
    
    db = SessionLocal()
    try:
        # 企業一覧を取得
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('dashboard_analysis.html', companies=companies)
    finally:
        db.close()


@bp.route('/dashboard-analysis/data/<int:company_id>/<int:fiscal_year_id>')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def dashboard_analysis_data(company_id, fiscal_year_id):
    """ダッシュボード分析データAPI"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement, BalanceSheet
        from app.utils.financial_calculator import calculate_all_ratios, get_ratio_status
        
        # 会計年度を確認
        fiscal_year = db.query(FiscalYear).join(Company).filter(
            FiscalYear.id == fiscal_year_id,
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'success': False, 'error': '会計年度が見つかりません'}), 404
        
        # 損益計算書を取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        # 貸借対照表を取得
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({
                'success': False,
                'error': '損益計算書または貸借対照表が登録されていません'
            }), 404
        
        # 財務指標を計算
        ratios = calculate_all_ratios(profit_loss, balance_sheet)
        
        # 各指標の状態を判定
        ratios_with_status = {}
        for category, indicators in ratios.items():
            ratios_with_status[category] = {}
            for name, value in indicators.items():
                ratios_with_status[category][name] = {
                    'value': value,
                    'status': get_ratio_status(name, value)
                }
        
        return jsonify({
            'success': True,
            'company_name': fiscal_year.company.name,
            'fiscal_year_name': fiscal_year.year_name,
            'profit_loss': {
                'sales': profit_loss.sales,
                'cost_of_sales': profit_loss.cost_of_sales,
                'gross_profit': profit_loss.gross_profit,
                'operating_expenses': profit_loss.operating_expenses,
                'operating_income': profit_loss.operating_income,
                'ordinary_income': profit_loss.ordinary_income,
                'net_income': profit_loss.net_income
            },
            'balance_sheet': {
                'current_assets': balance_sheet.current_assets,
                'fixed_assets': balance_sheet.fixed_assets,
                'total_assets': balance_sheet.total_assets,
                'current_liabilities': balance_sheet.current_liabilities,
                'fixed_liabilities': balance_sheet.fixed_liabilities,
                'total_liabilities': balance_sheet.total_liabilities,
                'total_equity': balance_sheet.total_equity
            },
            'ratios': ratios_with_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/fiscal-years/by-company/<int:company_id>')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def get_fiscal_years_by_company(company_id):
    """企業に紐づく会計年度一覧を取得するAPI"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    db = SessionLocal()
    try:
        # 企業を確認
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'success': False, 'error': '企業が見つかりません'}), 404
        
        # 会計年度一覧を取得
        fiscal_years = db.query(FiscalYear).filter(
            FiscalYear.company_id == company_id
        ).order_by(FiscalYear.start_date.desc()).all()
        
        fiscal_year_list = []
        for fy in fiscal_years:
            fiscal_year_list.append({
                'id': fy.id,
                'year_name': fy.year_name,
                'start_date': fy.start_date.strftime('%Y-%m-%d'),
                'end_date': fy.end_date.strftime('%Y-%m-%d')
            })
        
        return jsonify({
            'success': True,
            'fiscal_years': fiscal_year_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/dashboard-analysis/multi-year/<int:company_id>')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def dashboard_multi_year_data(company_id):
    """複数年度データAPI"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement, BalanceSheet
        
        # 企業を確認
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'success': False, 'error': '企業が見つかりません'}), 404
        
        # 会計年度一覧を取得
        fiscal_years = db.query(FiscalYear).filter(
            FiscalYear.company_id == company_id
        ).order_by(FiscalYear.start_date).all()
        
        multi_year_data = []
        for fy in fiscal_years:
            profit_loss = db.query(ProfitLossStatement).filter(
                ProfitLossStatement.fiscal_year_id == fy.id
            ).first()
            
            balance_sheet = db.query(BalanceSheet).filter(
                BalanceSheet.fiscal_year_id == fy.id
            ).first()
            
            if profit_loss and balance_sheet:
                multi_year_data.append({
                    'fiscal_year_name': fy.year_name,
                    'sales': profit_loss.sales,
                    'operating_income': profit_loss.operating_income,
                    'ordinary_income': profit_loss.ordinary_income,
                    'net_income': profit_loss.net_income,
                    'total_assets': balance_sheet.total_assets,
                    'total_liabilities': balance_sheet.total_liabilities,
                    'total_equity': balance_sheet.total_equity
                })
        
        return jsonify({
            'success': True,
            'company_name': company.name,
            'data': multi_year_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()



# ============================================================
# 経営シミュレーションルート
# ============================================================

@bp.route('/simulation')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def simulation():
    """経営シミュレーションページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('simulation.html', companies=companies)
    finally:
        db.close()


@bp.route('/simulation/execute')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def simulation_execute():
    """シミュレーション実行API"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    # パラメータを取得
    company_id = request.args.get('company_id', type=int)
    base_fiscal_year_id = request.args.get('base_fiscal_year_id', type=int)
    forecast_years = request.args.get('forecast_years', type=int)
    sales_growth_rate = request.args.get('sales_growth_rate', type=float)
    
    # オプションパラメータ
    operating_margin = request.args.get('operating_margin', type=float)
    ordinary_margin = request.args.get('ordinary_margin', type=float)
    net_margin = request.args.get('net_margin', type=float)
    asset_turnover = request.args.get('asset_turnover', type=float)
    debt_ratio = request.args.get('debt_ratio', type=float)
    
    if not all([company_id, base_fiscal_year_id, forecast_years, sales_growth_rate is not None]):
        return jsonify({'success': False, 'error': '必須パラメータが不足しています'}), 400
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement, BalanceSheet
        from app.utils.simulation_calculator import SimulationCalculator
        
        # 企業を確認
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'success': False, 'error': '企業が見つかりません'}), 404
        
        # ベース年度を確認
        base_fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == base_fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not base_fiscal_year:
            return jsonify({'success': False, 'error': 'ベース年度が見つかりません'}), 404
        
        # ベース年度の財務データを取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == base_fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == base_fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'success': False, 'error': 'ベース年度の財務データが見つかりません'}), 404
        
        # シミュレーションを実行
        forecast_data = SimulationCalculator.forecast_financials(
            base_sales=profit_loss.sales,
            base_operating_income=profit_loss.operating_income,
            base_ordinary_income=profit_loss.ordinary_income,
            base_net_income=profit_loss.net_income,
            base_total_assets=balance_sheet.total_assets,
            base_total_liabilities=balance_sheet.total_liabilities,
            base_total_equity=balance_sheet.total_equity,
            forecast_years=forecast_years,
            sales_growth_rate=sales_growth_rate,
            operating_margin=operating_margin,
            ordinary_margin=ordinary_margin,
            net_margin=net_margin,
            asset_turnover=asset_turnover,
            debt_ratio=debt_ratio
        )
        
        # 財務指標を計算
        forecast_data_with_ratios = SimulationCalculator.calculate_financial_ratios(forecast_data)
        
        return jsonify({
            'success': True,
            'company_name': company.name,
            'base_year_name': base_fiscal_year.year_name,
            'forecast_years': forecast_years,
            'sales_growth_rate': sales_growth_rate,
            'forecast_data': forecast_data_with_ratios
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/simulation/scenario')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"], ROLES["ADMIN"], ROLES["EMPLOYEE"])
def simulation_scenario():
    """シナリオ分析API"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'success': False, 'error': 'テナントIDが設定されていません'}), 400
    
    # パラメータを取得
    company_id = request.args.get('company_id', type=int)
    base_fiscal_year_id = request.args.get('base_fiscal_year_id', type=int)
    forecast_years = request.args.get('forecast_years', type=int)
    sales_growth_rate = request.args.get('sales_growth_rate', type=float)
    
    if not all([company_id, base_fiscal_year_id, forecast_years, sales_growth_rate is not None]):
        return jsonify({'success': False, 'error': '必須パラメータが不足しています'}), 400
    
    db = SessionLocal()
    try:
        from app.models_decision import ProfitLossStatement, BalanceSheet
        from app.utils.simulation_calculator import SimulationCalculator
        
        # 企業を確認
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'success': False, 'error': '企業が見つかりません'}), 404
        
        # ベース年度を確認
        base_fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == base_fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not base_fiscal_year:
            return jsonify({'success': False, 'error': 'ベース年度が見つかりません'}), 404
        
        # ベース年度の財務データを取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == base_fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == base_fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'success': False, 'error': 'ベース年度の財務データが見つかりません'}), 404
        
        # シナリオ分析を実行
        scenarios = SimulationCalculator.create_scenario_forecasts(
            base_sales=profit_loss.sales,
            base_operating_income=profit_loss.operating_income,
            base_ordinary_income=profit_loss.ordinary_income,
            base_net_income=profit_loss.net_income,
            base_total_assets=balance_sheet.total_assets,
            base_total_liabilities=balance_sheet.total_liabilities,
            base_total_equity=balance_sheet.total_equity,
            forecast_years=forecast_years,
            base_growth_rate=sales_growth_rate
        )
        
        # 各シナリオの財務指標を計算
        scenarios_with_ratios = {
            'optimistic': SimulationCalculator.calculate_financial_ratios(scenarios['optimistic']),
            'standard': SimulationCalculator.calculate_financial_ratios(scenarios['standard']),
            'pessimistic': SimulationCalculator.calculate_financial_ratios(scenarios['pessimistic'])
        }
        
        return jsonify({
            'success': True,
            'company_name': company.name,
            'base_year_name': base_fiscal_year.year_name,
            'forecast_years': forecast_years,
            'base_growth_rate': sales_growth_rate,
            'scenarios': scenarios_with_ratios
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# 詳細財務分析ルート
# ============================================================

@bp.route('/financial-analysis-detailed')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def financial_analysis_detailed():
    """詳細財務分析ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        # テナントの企業一覧を取得
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('financial_analysis_detailed.html', companies=companies)
    finally:
        db.close()


@bp.route('/financial-analysis-detailed/analyze')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def financial_analysis_detailed_analyze():
    """詳細財務分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    company_id = request.args.get('company_id', type=int)
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    
    if not company_id or not fiscal_year_id:
        return jsonify({'error': '企業IDと会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.advanced_financial_analysis import calculate_all_indicators
        from ..models_decision import ProfitLossStatement, BalanceSheet
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 当期の財務データを取得
        current_pl = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        current_bs = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not current_pl or not current_bs:
            return jsonify({'error': '財務データが見つかりません'}), 404
        
        # 前期の財務データを取得（成長力指標用）
        # 前期の会計年度を取得
        previous_fiscal_years = db.query(FiscalYear).filter(
            FiscalYear.company_id == company_id,
            FiscalYear.start_date < fiscal_year.start_date
        ).order_by(FiscalYear.start_date.desc()).all()
        
        previous_pl = None
        previous_bs = None
        if previous_fiscal_years:
            previous_fiscal_year = previous_fiscal_years[0]
            previous_pl = db.query(ProfitLossStatement).filter(
                ProfitLossStatement.fiscal_year_id == previous_fiscal_year.id
            ).first()
            previous_bs = db.query(BalanceSheet).filter(
                BalanceSheet.fiscal_year_id == previous_fiscal_year.id
            ).first()
        
        # 当期PLデータを辞書に変換
        current_pl_data = {
            'sales': current_pl.sales,
            'cost_of_sales': current_pl.cost_of_sales,
            'gross_profit': current_pl.gross_profit,
            'operating_income': current_pl.operating_income,
            'ordinary_income': current_pl.ordinary_income,
            'net_income': current_pl.net_income,
            'employees': company.employee_count or 1,  # ゼロ除算を避けるため
            'labor_cost': current_pl.operating_expenses * 0.4,  # 仮の労務費（販管費の40%と仮定）
            'interest_expense': current_pl.non_operating_expenses  # 仮の支払利息
        }
        
        # 当期BSデータを辞書に変換
        current_bs_data = {
            'current_assets': current_bs.current_assets,
            'fixed_assets': current_bs.fixed_assets,
            'total_assets': current_bs.total_assets,
            'current_liabilities': current_bs.current_liabilities,
            'fixed_liabilities': current_bs.fixed_liabilities,
            'total_liabilities': current_bs.total_liabilities,
            'net_assets': current_bs.total_equity,
            'long_term_liabilities': current_bs.fixed_liabilities,
            'quick_assets': current_bs.current_assets * 0.7,  # 仮の当座資産（流動資産の70%と仮定）
            'accounts_receivable': current_bs.current_assets * 0.4,  # 仮の売上債権（流動資産の40%と仮定）
            'inventory': current_bs.current_assets * 0.3,  # 仮の棚卸資産（流動資産の30%と仮定）
            'accounts_payable': current_bs.current_liabilities * 0.5  # 仮の買入債務（流動負債の50%と仮定）
        }
        
        # 前期データを辞書に変換（存在する場合）
        previous_pl_data = None
        previous_bs_data = None
        if previous_pl and previous_bs:
            previous_pl_data = {
                'sales': previous_pl.sales,
                'employees': company.employee_count or 1
            }
            previous_bs_data = {
                'total_assets': previous_bs.total_assets,
                'net_assets': previous_bs.total_equity
            }
        
        # すべての財務指標を計算
        indicators = calculate_all_indicators(
            current_pl=current_pl_data,
            current_bs=current_bs_data,
            previous_pl=previous_pl_data,
            previous_bs=previous_bs_data
        )
        
        # 結果を返す
        return jsonify({
            'company_name': company.name,
            'fiscal_year_name': fiscal_year.year_name,
            'start_date': fiscal_year.start_date.strftime('%Y年%m月%d日'),
            'end_date': fiscal_year.end_date.strftime('%Y年%m月%d日'),
            'growth': indicators['growth'],
            'profitability': indicators['profitability'],
            'financial_strength': indicators['financial_strength'],
            'productivity': indicators['productivity']
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# 損益分岐点分析ルート
# ============================================================

@bp.route('/breakeven-analysis')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def breakeven_analysis():
    """損益分岐点分析ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        # テナントの企業一覧を取得
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('breakeven_analysis.html', companies=companies)
    finally:
        db.close()


@bp.route('/breakeven-analysis/analyze')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def breakeven_analysis_analyze():
    """損益分岐点分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    company_id = request.args.get('company_id', type=int)
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    
    if not company_id or not fiscal_year_id:
        return jsonify({'error': '企業IDと会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.breakeven_analysis import analyze_cost_volume_profit, estimate_cost_structure
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 損益計算書を取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss:
            return jsonify({'error': '損益計算書が見つかりません'}), 404
        
        # 費用構造を推定
        cost_structure = estimate_cost_structure(
            sales=profit_loss.sales,
            cost_of_sales=profit_loss.cost_of_sales,
            operating_expenses=profit_loss.operating_expenses,
            operating_income=profit_loss.operating_income
        )
        
        # CVP分析を実行
        cvp_result = analyze_cost_volume_profit(
            sales=profit_loss.sales,
            variable_costs=cost_structure['variable_costs'],
            fixed_costs=cost_structure['fixed_costs']
        )
        
        # 結果を返す
        return jsonify({
            'company_name': company.name,
            'fiscal_year_name': fiscal_year.year_name,
            'start_date': fiscal_year.start_date.strftime('%Y年%m月%d日'),
            'end_date': fiscal_year.end_date.strftime('%Y年%m月%d日'),
            **cvp_result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# 予算管理ルート
# ============================================================

@bp.route('/budget')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def budget_management():
    """予算管理ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        # テナントの企業一覧を取得
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('budget_management.html', companies=companies)
    finally:
        db.close()


@bp.route('/budget/analyze')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def budget_analyze():
    """予算vs実績分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.budget_analysis import analyze_budget_vs_actual, calculate_budget_achievement_summary
        from ..models_decision import Budget
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 予算を取得
        budget = db.query(Budget).filter(
            Budget.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not budget:
            return jsonify({
                'error': '予算が登録されていません',
                'has_budget': False
            })
        
        # 実績（損益計算書と貸借対照表）を取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'error': '実績データが見つかりません'}), 404
        
        # 予算データを辞書に変換
        budget_data = {
            'budget_sales': float(budget.budget_sales or 0),
            'budget_cost_of_sales': float(budget.budget_cost_of_sales or 0),
            'budget_gross_profit': float(budget.budget_gross_profit or 0),
            'budget_operating_expenses': float(budget.budget_operating_expenses or 0),
            'budget_operating_income': float(budget.budget_operating_income or 0),
            'budget_ordinary_income': float(budget.budget_ordinary_income or 0),
            'budget_net_income': float(budget.budget_net_income or 0),
            'budget_current_assets': float(budget.budget_current_assets or 0),
            'budget_fixed_assets': float(budget.budget_fixed_assets or 0),
            'budget_total_assets': float(budget.budget_total_assets or 0),
            'budget_current_liabilities': float(budget.budget_current_liabilities or 0),
            'budget_fixed_liabilities': float(budget.budget_fixed_liabilities or 0),
            'budget_total_liabilities': float(budget.budget_total_liabilities or 0),
            'budget_total_equity': float(budget.budget_total_equity or 0)
        }
        
        # 実績データを辞書に変換
        actual_data = {
            'sales': float(profit_loss.sales or 0),
            'cost_of_sales': float(profit_loss.cost_of_sales or 0),
            'gross_profit': float(profit_loss.gross_profit or 0),
            'operating_expenses': float(profit_loss.operating_expenses or 0),
            'operating_income': float(profit_loss.operating_income or 0),
            'ordinary_income': float(profit_loss.ordinary_income or 0),
            'net_income': float(profit_loss.net_income or 0),
            'current_assets': float(balance_sheet.current_assets or 0),
            'fixed_assets': float(balance_sheet.fixed_assets or 0),
            'total_assets': float(balance_sheet.total_assets or 0),
            'current_liabilities': float(balance_sheet.current_liabilities or 0),
            'fixed_liabilities': float(balance_sheet.fixed_liabilities or 0),
            'total_liabilities': float(balance_sheet.total_liabilities or 0),
            'total_equity': float(balance_sheet.total_equity or 0)
        }
        
        # 予算vs実績分析を実行
        analysis_result = analyze_budget_vs_actual(budget_data, actual_data)
        
        # 予算達成度サマリーを計算
        summary = calculate_budget_achievement_summary(analysis_result)
        
        # 結果を返す
        return jsonify({
            'has_budget': True,
            'budget': {
                'id': budget.id,
                **budget_data
            },
            'pl': analysis_result['pl'],
            'bs': analysis_result['bs'],
            'summary': summary
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/budget', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def budget_create():
    """予算を登録"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    fiscal_year_id = data.get('fiscal_year_id')
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..models_decision import Budget
        
        # 会計年度の存在確認
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業のテナント確認
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 既存の予算があるか確認
        existing_budget = db.query(Budget).filter(
            Budget.fiscal_year_id == fiscal_year_id
        ).first()
        
        if existing_budget:
            return jsonify({'error': 'この会計年度の予算は既に登録されています'}), 400
        
        # 予算を作成
        budget = Budget(
            fiscal_year_id=fiscal_year_id,
            budget_sales=data.get('budget_sales'),
            budget_cost_of_sales=data.get('budget_cost_of_sales'),
            budget_gross_profit=data.get('budget_gross_profit'),
            budget_operating_expenses=data.get('budget_operating_expenses'),
            budget_operating_income=data.get('budget_operating_income'),
            budget_non_operating_income=data.get('budget_non_operating_income'),
            budget_non_operating_expenses=data.get('budget_non_operating_expenses'),
            budget_ordinary_income=data.get('budget_ordinary_income'),
            budget_extraordinary_income=data.get('budget_extraordinary_income'),
            budget_extraordinary_loss=data.get('budget_extraordinary_loss'),
            budget_income_before_tax=data.get('budget_income_before_tax'),
            budget_income_tax=data.get('budget_income_tax'),
            budget_net_income=data.get('budget_net_income'),
            budget_current_assets=data.get('budget_current_assets'),
            budget_fixed_assets=data.get('budget_fixed_assets'),
            budget_total_assets=data.get('budget_total_assets'),
            budget_current_liabilities=data.get('budget_current_liabilities'),
            budget_fixed_liabilities=data.get('budget_fixed_liabilities'),
            budget_total_liabilities=data.get('budget_total_liabilities'),
            budget_total_equity=data.get('budget_total_equity'),
            notes=data.get('notes')
        )
        
        db.add(budget)
        db.commit()
        
        return jsonify({'message': '予算を登録しました', 'id': budget.id})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/budget/<int:budget_id>', methods=['PUT'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def budget_update(budget_id):
    """予算を更新"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    db = SessionLocal()
    try:
        from ..models_decision import Budget
        
        # 予算を取得
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        
        if not budget:
            return jsonify({'error': '予算が見つかりません'}), 404
        
        # 会計年度の企業のテナント確認
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == budget.fiscal_year_id
        ).first()
        
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 予算を更新
        budget.budget_sales = data.get('budget_sales')
        budget.budget_cost_of_sales = data.get('budget_cost_of_sales')
        budget.budget_gross_profit = data.get('budget_gross_profit')
        budget.budget_operating_expenses = data.get('budget_operating_expenses')
        budget.budget_operating_income = data.get('budget_operating_income')
        budget.budget_non_operating_income = data.get('budget_non_operating_income')
        budget.budget_non_operating_expenses = data.get('budget_non_operating_expenses')
        budget.budget_ordinary_income = data.get('budget_ordinary_income')
        budget.budget_extraordinary_income = data.get('budget_extraordinary_income')
        budget.budget_extraordinary_loss = data.get('budget_extraordinary_loss')
        budget.budget_income_before_tax = data.get('budget_income_before_tax')
        budget.budget_income_tax = data.get('budget_income_tax')
        budget.budget_net_income = data.get('budget_net_income')
        budget.budget_current_assets = data.get('budget_current_assets')
        budget.budget_fixed_assets = data.get('budget_fixed_assets')
        budget.budget_total_assets = data.get('budget_total_assets')
        budget.budget_current_liabilities = data.get('budget_current_liabilities')
        budget.budget_fixed_liabilities = data.get('budget_fixed_liabilities')
        budget.budget_total_liabilities = data.get('budget_total_liabilities')
        budget.budget_total_equity = data.get('budget_total_equity')
        budget.notes = data.get('notes')
        
        db.commit()
        
        return jsonify({'message': '予算を更新しました'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# 借入金許容限度額分析ルート
# ============================================================

@bp.route('/debt-capacity')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def debt_capacity_analysis():
    """借入金許容限度額分析ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        # テナントの企業一覧を取得
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('debt_capacity_analysis.html', companies=companies)
    finally:
        db.close()


@bp.route('/debt-capacity/analyze')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def debt_capacity_analyze():
    """借入金許容限度額分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.debt_capacity_analysis import calculate_debt_capacity, evaluate_debt_health
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 損益計算書と貸借対照表を取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'error': '財務データが見つかりません'}), 404
        
        # 年間キャッシュフローを計算（簡易的に営業利益を使用）
        annual_cash_flow = float(profit_loss.operating_income or 0)
        
        # 支払利息（簡易的に営業外費用の50%と仮定）
        interest_expense = float(profit_loss.non_operating_expenses or 0) * 0.5
        
        # 借入金許容限度額を計算
        capacity = calculate_debt_capacity(
            total_assets=float(balance_sheet.total_assets or 0),
            total_liabilities=float(balance_sheet.total_liabilities or 0),
            total_equity=float(balance_sheet.total_equity or 0),
            operating_income=float(profit_loss.operating_income or 0),
            interest_expense=interest_expense,
            annual_cash_flow=annual_cash_flow
        )
        
        # 借入金健全性を評価
        health = evaluate_debt_health(
            equity_ratio=capacity['current_equity_ratio'],
            debt_ratio=capacity['current_debt_ratio'],
            debt_service_years=capacity['debt_service_years'],
            interest_coverage_ratio=capacity['interest_coverage_ratio']
        )
        
        return jsonify({
            'capacity': capacity,
            'health': health
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/debt-capacity/method1')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def debt_capacity_method1():
    """借入金許容限度額分析 Method1"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.debt_capacity_method13 import calculate_debt_capacity_method1
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # Method1を計算
        result = calculate_debt_capacity_method1(fiscal_year_id)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/debt-capacity/method3')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def debt_capacity_method3():
    """借入金許容限度額分析 Method3"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    standard_rate = request.args.get('standard_rate', type=float)
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.debt_capacity_method13 import calculate_debt_capacity_method3
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # Method3を計算
        result = calculate_debt_capacity_method3(fiscal_year_id, standard_rate)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/debt-capacity/repayment-plan')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def debt_capacity_repayment_plan():
    """返済計画を計算"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    loan_amount = request.args.get('loan_amount', type=float)
    interest_rate = request.args.get('interest_rate', type=float)
    repayment_years = request.args.get('repayment_years', type=int)
    
    if not loan_amount or not repayment_years:
        return jsonify({'error': 'パラメータが不足しています'}), 400
    
    try:
        from ..utils.debt_capacity_analysis import calculate_debt_repayment_plan
        
        repayment_plan = calculate_debt_repayment_plan(
            debt_amount=loan_amount,
            annual_interest_rate=interest_rate,
            repayment_years=repayment_years
        )
        
        return jsonify({'repayment_plan': repayment_plan})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



# ============================================================
# 資金繰り計画
# ============================================================

@bp.route('/cash-flow-planning')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def cash_flow_planning():
    """資金繰り計画ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('cash_flow_planning.html', companies=companies)
    finally:
        db.close()


@bp.route('/cash-flow-planning/generate', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def generate_cash_flow_plan():
    """資金繰り計画を生成"""
    from app.utils.cash_flow_planning import generate_annual_cash_flow_plan, calculate_required_financing
    
    data = request.json
    
    # 年間の資金繰り計画を生成
    cash_flow_plan = generate_annual_cash_flow_plan(
        beginning_balance=data['beginning_balance'],
        monthly_sales_revenue=data['monthly_sales_revenue'],
        monthly_purchase_payment=data['monthly_purchase_payment'],
        monthly_personnel_cost=data['monthly_personnel_cost'],
        monthly_rent=data['monthly_rent'],
        monthly_utilities=data['monthly_utilities'],
        monthly_other_expenses=data['monthly_other_expenses'],
        loan_repayment=data.get('loan_repayment', 0),
        tax_payment_month=data.get('tax_payment_month'),
        tax_payment_amount=data.get('tax_payment_amount', 0)
    )
    
    # 資金不足を検出
    financing_info = calculate_required_financing(
        cash_flow_plan,
        minimum_balance=data['minimum_balance']
    )
    
    return jsonify({
        'cash_flow_plan': cash_flow_plan,
        'minimum_balance': data['minimum_balance'],
        **financing_info
    })


@bp.route('/cash-flow-planning/simulate-financing', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def simulate_financing():
    """資金調達の影響をシミュレーション"""
    from app.utils.cash_flow_planning import simulate_financing_impact
    
    data = request.json
    
    updated_plan = simulate_financing_impact(
        cash_flow_plan=data['cash_flow_plan'],
        financing_amount=data['financing_amount'],
        financing_month=data['financing_month'],
        interest_rate=data['interest_rate']
    )
    
    return jsonify({
        'updated_plan': updated_plan
    })



# ============================================================
# 内部留保シミュレーション
# ============================================================

@bp.route('/retained-earnings-simulation')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def retained_earnings_simulation():
    """内部留保シミュレーションページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('retained_earnings_simulation.html', companies=companies)
    finally:
        db.close()


@bp.route('/retained-earnings-simulation/simulate')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def retained_earnings_simulation_simulate():
    """内部留保シミュレーションを実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    company_id = request.args.get('company_id', type=int)
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    years = request.args.get('years', type=int, default=10)
    dividend_payout_ratio = request.args.get('dividend_payout_ratio', type=float, default=0.3)
    growth_rate = request.args.get('growth_rate', type=float, default=0.0)
    
    if not company_id or not fiscal_year_id:
        return jsonify({'error': '企業IDと会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.retained_earnings_simulation import simulate_retained_earnings
        from app.models_decision import ProfitLossStatement, BalanceSheet
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 財務データを取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'error': '財務データが見つかりません'}), 404
        
        # シミュレーションを実行
        result = simulate_retained_earnings(
            current_net_assets=float(balance_sheet.total_equity),
            annual_net_income=float(profit_loss.net_income),
            dividend_payout_ratio=dividend_payout_ratio,
            years=years,
            growth_rate=growth_rate
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/retained-earnings-simulation/scenarios')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def retained_earnings_simulation_scenarios():
    """複数シナリオで内部留保シミュレーションを実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    company_id = request.args.get('company_id', type=int)
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    years = request.args.get('years', type=int, default=10)
    growth_rate = request.args.get('growth_rate', type=float, default=0.0)
    
    # 配当性向のリストを取得（カンマ区切り）
    payout_ratios_str = request.args.get('payout_ratios', '')
    
    if not company_id or not fiscal_year_id:
        return jsonify({'error': '企業IDと会計年度IDを指定してください'}), 400
    
    if not payout_ratios_str:
        return jsonify({'error': '配当性向のリストを指定してください'}), 400
    
    try:
        # 配当性向のリストをパース
        payout_ratios = [float(r.strip()) for r in payout_ratios_str.split(',')]
    except ValueError:
        return jsonify({'error': '配当性向の形式が不正です'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.retained_earnings_simulation import simulate_retained_earnings_scenarios
        from app.models_decision import ProfitLossStatement, BalanceSheet
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 財務データを取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'error': '財務データが見つかりません'}), 404
        
        # シナリオ分析を実行
        result = simulate_retained_earnings_scenarios(
            current_net_assets=float(balance_sheet.total_equity),
            annual_net_income=float(profit_loss.net_income),
            dividend_payout_ratios=payout_ratios,
            years=years,
            growth_rate=growth_rate
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# 貢献度分析
# ============================================================

@bp.route('/internal-reserve-usage/simulate')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def internal_reserve_usage_simulate():
    """内部留保使途（再投資 vs 負債返済）シミュレーション"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    company_id = request.args.get('company_id', type=int)
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    years = request.args.get('years', type=int, default=3)
    dividend_payout_ratio = request.args.get('dividend_payout_ratio', type=float, default=0.3)
    reinvestment_ratio = request.args.get('reinvestment_ratio', type=float, default=0.5)
    growth_rate = request.args.get('growth_rate', type=float, default=0.0)
    
    if not company_id or not fiscal_year_id:
        return jsonify({'error': '企業IDと会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.retained_earnings_simulation import simulate_internal_reserve_usage
        from app.models_decision import ProfitLossStatement, BalanceSheet
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 財務データを取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'error': '財務データが見つかりません'}), 404
        
        # シミュレーションを実行
        result = simulate_internal_reserve_usage(
            current_net_assets=float(balance_sheet.total_equity),
            current_total_assets=float(balance_sheet.total_assets),
            current_liabilities=float(balance_sheet.total_liabilities),
            annual_net_income=float(profit_loss.net_income),
            dividend_payout_ratio=dividend_payout_ratio,
            reinvestment_ratio=reinvestment_ratio,
            years=years,
            growth_rate=growth_rate
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/internal-reserve-usage/scenarios')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def internal_reserve_usage_scenarios():
    """複数シナリオで内部留保使途をシミュレーション"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    company_id = request.args.get('company_id', type=int)
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    years = request.args.get('years', type=int, default=3)
    dividend_payout_ratio = request.args.get('dividend_payout_ratio', type=float, default=0.3)
    growth_rate = request.args.get('growth_rate', type=float, default=0.0)
    
    # 再投資比率のリストを取得（カンマ区切り）
    reinvestment_ratios_str = request.args.get('reinvestment_ratios', '')
    
    if not company_id or not fiscal_year_id:
        return jsonify({'error': '企業IDと会計年度IDを指定してください'}), 400
    
    if not reinvestment_ratios_str:
        return jsonify({'error': '再投資比率のリストを指定してください'}), 400
    
    try:
        # 再投資比率のリストをパース
        reinvestment_ratios = [float(r.strip()) for r in reinvestment_ratios_str.split(',')]
    except ValueError:
        return jsonify({'error': '再投資比率の形式が不正です'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.retained_earnings_simulation import simulate_internal_reserve_scenarios
        from app.models_decision import ProfitLossStatement, BalanceSheet
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.company_id == company_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 財務データを取得
        profit_loss = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        balance_sheet = db.query(BalanceSheet).filter(
            BalanceSheet.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not profit_loss or not balance_sheet:
            return jsonify({'error': '財務データが見つかりません'}), 404
        
        # シナリオ分析を実行
        result = simulate_internal_reserve_scenarios(
            current_net_assets=float(balance_sheet.total_equity),
            current_total_assets=float(balance_sheet.total_assets),
            current_liabilities=float(balance_sheet.total_liabilities),
            annual_net_income=float(profit_loss.net_income),
            dividend_payout_ratio=dividend_payout_ratio,
            reinvestment_ratios=reinvestment_ratios,
            years=years,
            growth_rate=growth_rate
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/contribution-analysis')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def contribution_analysis():
    """貢献度分析ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('contribution_analysis.html', companies=companies)
    finally:
        db.close()


@bp.route('/contribution-analysis/analyze', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def contribution_analysis_analyze():
    """貢献度分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    segments = data.get('segments', [])
    common_fixed_cost = float(data.get('common_fixed_cost', 0))
    
    if not segments:
        return jsonify({'error': 'セグメント情報を指定してください'}), 400
    
    try:
        from ..utils.contribution_analyzer import analyze_product_mix
        
        # 貢献度分析を実行
        result = analyze_product_mix(segments, common_fixed_cost)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================
# 最小二乗法による予測
# ============================================================

@bp.route('/least-squares-forecast')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def least_squares_forecast():
    """最小二乗法による予測ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.tenant_id == tenant_id).all()
        return render_template('least_squares_forecast.html', companies=companies)
    finally:
        db.close()


@bp.route('/least-squares-forecast/forecast')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def least_squares_forecast_forecast():
    """最小二乗法による予測を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    company_id = request.args.get('company_id', type=int)
    forecast_years = request.args.get('forecast_years', type=int, default=5)
    
    if not company_id:
        return jsonify({'error': '企業IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.least_squares_forecaster import forecast_sales
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # 会計年度と財務データを取得
        fiscal_years = db.query(FiscalYear).filter(
            FiscalYear.company_id == company_id
        ).order_by(FiscalYear.start_date).all()
        
        if len(fiscal_years) < 2:
            return jsonify({'error': '最小2年分の会計年度データが必要です'}), 400
        
        # 売上高データを収集
        sales_data = []
        operating_income_data = []
        net_income_data = []
        
        for fy in fiscal_years:
            profit_loss = db.query(ProfitLossStatement).filter(
                ProfitLossStatement.fiscal_year_id == fy.id
            ).first()
            
            if profit_loss:
                # 年度番号を抽出（例: "2023年度" -> 2023）
                year_num = int(fy.year_name.replace('年度', ''))
                
                sales_data.append({
                    'year': year_num,
                    'sales': float(profit_loss.sales)
                })
                
                operating_income_data.append({
                    'year': year_num,
                    'sales': float(profit_loss.operating_income)
                })
                
                net_income_data.append({
                    'year': year_num,
                    'sales': float(profit_loss.net_income)
                })
        
        if len(sales_data) < 2:
            return jsonify({'error': '最小2年分の財務データが必要です'}), 400
        
        # 各指標の予測を実行
        sales_forecast = forecast_sales(sales_data, forecast_years)
        operating_income_forecast = forecast_sales(operating_income_data, forecast_years)
        net_income_forecast = forecast_sales(net_income_data, forecast_years)
        
        return jsonify({
            'sales': sales_forecast,
            'operating_income': operating_income_forecast,
            'net_income': net_income_forecast
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# 差額原価収益分析
# ============================================================

@bp.route('/differential-analysis')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def differential_analysis():
    """差額原価収益分析ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    return render_template('differential_cost_analysis.html')


@bp.route('/differential-analysis/general', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def differential_analysis_general():
    """一般的な差額分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.differential_analysis import calculate_differential_profit
        
        result = calculate_differential_profit(
            scenario_a_sales=float(data.get('scenario_a_sales', 0)),
            scenario_a_variable_cost=float(data.get('scenario_a_variable_cost', 0)),
            scenario_a_fixed_cost=float(data.get('scenario_a_fixed_cost', 0)),
            scenario_b_sales=float(data.get('scenario_b_sales', 0)),
            scenario_b_variable_cost=float(data.get('scenario_b_variable_cost', 0)),
            scenario_b_fixed_cost=float(data.get('scenario_b_fixed_cost', 0))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/differential-analysis/make-or-buy', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def differential_analysis_make_or_buy():
    """自製か購入か分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.differential_analysis import analyze_make_or_buy
        
        result = analyze_make_or_buy(
            make_variable_cost=float(data.get('make_variable_cost', 0)),
            make_fixed_cost=float(data.get('make_fixed_cost', 0)),
            buy_price=float(data.get('buy_price', 0)),
            quantity=int(data.get('quantity', 0))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/differential-analysis/special-order', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def differential_analysis_special_order():
    """特別注文の受諾可否分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.differential_analysis import analyze_accept_or_reject_order
        
        result = analyze_accept_or_reject_order(
            regular_price=float(data.get('regular_price', 0)),
            special_order_price=float(data.get('special_order_price', 0)),
            variable_cost=float(data.get('variable_cost', 0)),
            quantity=int(data.get('quantity', 0)),
            additional_fixed_cost=float(data.get('additional_fixed_cost', 0))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/differential-analysis/continue-or-discontinue', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def differential_analysis_continue_or_discontinue():
    """事業継続・撤退分析を実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.differential_analysis import analyze_continue_or_discontinue
        
        result = analyze_continue_or_discontinue(
            sales=float(data.get('sales', 0)),
            variable_cost=float(data.get('variable_cost', 0)),
            direct_fixed_cost=float(data.get('direct_fixed_cost', 0)),
            avoidable_fixed_cost=float(data.get('avoidable_fixed_cost', 0)),
            unavoidable_fixed_cost=float(data.get('unavoidable_fixed_cost', 0))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================
# 労務費管理計画
# ============================================================

@bp.route('/labor-cost-planning')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def labor_cost_planning():
    """労務費管理計画ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    return render_template('labor_cost_planning.html')


@bp.route('/labor-cost-planning/calculate', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def labor_cost_planning_calculate():
    """労務費計画を計算"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.labor_cost_planner import plan_labor_cost
        
        result = plan_labor_cost(
            current_employee_count=int(data.get('current_employee_count', 0)),
            planned_employee_count=int(data.get('planned_employee_count', 0)),
            average_salary=float(data.get('average_salary', 0)),
            bonus_months=float(data.get('bonus_months', 2.0)),
            social_insurance_rate=float(data.get('social_insurance_rate', 0.15)),
            welfare_rate=float(data.get('welfare_rate', 0.05)),
            other_rate=float(data.get('other_rate', 0.02))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/labor-cost-planning/analyze', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def labor_cost_planning_analyze():
    """労務費効率性を分析"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.labor_cost_planner import analyze_labor_cost_efficiency
        
        result = analyze_labor_cost_efficiency(
            total_labor_cost=float(data.get('total_labor_cost', 0)),
            sales=float(data.get('sales', 0)),
            operating_income=float(data.get('operating_income', 0)),
            employee_count=int(data.get('employee_count', 1))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================
# 設備投資計画
# ============================================================

@bp.route('/capital-investment')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def capital_investment():
    """設備投資計画ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    return render_template('capital_investment_planning.html')


@bp.route('/capital-investment/evaluate', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def capital_investment_evaluate():
    """投資案件を評価"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.capital_investment_planner import evaluate_investment
        
        result = evaluate_investment(
            initial_investment=float(data.get('initial_investment', 0)),
            annual_cash_flows=[float(cf) for cf in data.get('annual_cash_flows', [])],
            discount_rate=float(data.get('discount_rate', 5)),
            project_name=data.get('project_name', '投資案件')
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/capital-investment/replacement', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def capital_investment_replacement():
    """設備更新を評価"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.capital_investment_planner import calculate_equipment_replacement
        
        result = calculate_equipment_replacement(
            old_equipment_book_value=float(data.get('old_equipment_book_value', 0)),
            old_equipment_salvage_value=float(data.get('old_equipment_salvage_value', 0)),
            old_equipment_annual_cost=float(data.get('old_equipment_annual_cost', 0)),
            new_equipment_cost=float(data.get('new_equipment_cost', 0)),
            new_equipment_salvage_value=float(data.get('new_equipment_salvage_value', 0)),
            new_equipment_annual_cost=float(data.get('new_equipment_annual_cost', 0)),
            useful_life=int(data.get('useful_life', 10)),
            discount_rate=float(data.get('discount_rate', 5))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================
# 主要運転資金計画
# ============================================================

@bp.route('/working-capital-planning')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def working_capital_planning():
    """主要運転資金計画ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    return render_template('working_capital_planning.html')


@bp.route('/working-capital-planning/calculate', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def working_capital_planning_calculate():
    """運転資金を計算"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.working_capital_planner import plan_working_capital
        
        result = plan_working_capital(
            sales=float(data.get('sales', 0)),
            cost_of_sales=float(data.get('cost_of_sales', 0)),
            accounts_receivable_days=int(data.get('accounts_receivable_days', 30)),
            inventory_days=int(data.get('inventory_days', 30)),
            accounts_payable_days=int(data.get('accounts_payable_days', 30))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/working-capital-planning/increase', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def working_capital_planning_increase():
    """運転資金増加額を計算"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.working_capital_planner import calculate_required_working_capital_increase
        
        result = calculate_required_working_capital_increase(
            current_sales=float(data.get('current_sales', 0)),
            planned_sales=float(data.get('planned_sales', 0)),
            current_working_capital=float(data.get('current_working_capital', 0))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================
# 資金調達返済計画
# ============================================================

@bp.route('/financing-repayment')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def financing_repayment():
    """資金調達返済計画ページ"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return redirect(url_for('decision.index'))
    
    return render_template('financing_repayment_planning.html')


@bp.route('/financing-repayment/plan', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def financing_repayment_plan():
    """資金調達計画を作成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.financing_repayment_planner import plan_financing_repayment
        
        result = plan_financing_repayment(
            required_funds=float(data.get('required_funds', 0)),
            equity_ratio=float(data.get('equity_ratio', 30)),
            loan_interest_rate=float(data.get('loan_interest_rate', 2.5)),
            loan_term_years=int(data.get('loan_term_years', 10)),
            payment_frequency=data.get('payment_frequency', 'monthly')
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/financing-repayment/schedule', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def financing_repayment_schedule():
    """返済スケジュールを生成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.financing_repayment_planner import generate_amortization_schedule
        
        schedule = generate_amortization_schedule(
            principal=float(data.get('principal', 0)),
            annual_interest_rate=float(data.get('annual_interest_rate', 2.5)),
            term_years=int(data.get('term_years', 10)),
            payment_frequency='monthly'
        )
        
        return jsonify({'schedule': schedule})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/financing-repayment/refinance', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def financing_repayment_refinance():
    """借り換えを分析"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    
    try:
        from ..utils.financing_repayment_planner import calculate_refinancing_benefit
        
        result = calculate_refinancing_benefit(
            current_loan_balance=float(data.get('current_loan_balance', 0)),
            current_interest_rate=float(data.get('current_interest_rate', 3.0)),
            remaining_term_years=int(data.get('remaining_term_years', 8)),
            new_interest_rate=float(data.get('new_interest_rate', 2.0)),
            refinancing_cost=float(data.get('refinancing_cost', 0))
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



@bp.route('/debt-capacity/method2')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def debt_capacity_method2():
    """借入金許容限度額分析 Method2（安全金利法）"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    target_interest_burden_ratio = request.args.get('target_interest_burden_ratio', type=float, default=0.10)
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.debt_capacity_analysis import calculate_debt_capacity_method2
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # PLを取得
        pl = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not pl:
            return jsonify({'error': 'PLが見つかりません'}), 404
        
        # 基礎データ
        gross_profit = float(pl.gross_profit or 0)
        operating_income = float(pl.operating_income or 0)
        interest_expense = float(pl.non_operating_expenses or 0)  # 簡易的に営業外費用を利息とする
        
        # 平均金利（仮に3%とする、実際はユーザ入力が必要）
        average_interest_rate = 3.0
        
        # Method2を計算
        result = calculate_debt_capacity_method2(
            gross_profit=gross_profit,
            operating_income=operating_income,
            interest_expense=interest_expense,
            average_interest_rate=average_interest_rate,
            target_interest_burden_ratio=target_interest_burden_ratio
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/debt-capacity/method4')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def debt_capacity_method4():
    """借入金許容限度額分析 Method4（金利階段表）"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    standard_rate = request.args.get('standard_rate', type=float, default=0.10)
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.debt_capacity_method13 import calculate_debt_capacity_rate_table
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # Method4（金利階段表）を計算
        result = calculate_debt_capacity_rate_table(fiscal_year_id, standard_rate)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/cash-flow/integrated-monthly-plan')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def integrated_monthly_cash_flow_plan():
    """統合月次資金繰り表を生成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    beginning_cash_balance = request.args.get('beginning_cash_balance', type=float, default=1000000)
    minimum_cash_balance = request.args.get('minimum_cash_balance', type=float, default=500000)
    
    if not fiscal_year_id:
        return jsonify({'error': '会計年度IDを指定してください'}), 400
    
    db = SessionLocal()
    try:
        from ..utils.integrated_cash_flow_planner import (
            generate_integrated_monthly_cash_flow,
            calculate_operating_cash_flow_from_pl,
            calculate_investment_cash_flow_from_capex,
            calculate_financing_cash_flow_from_debt,
            generate_shortage_alert_message,
            suggest_financing_solution
        )
        from ..utils.repayment_plan_formatter import format_cash_flow_table_for_ui
        
        # 会計年度情報を取得
        fiscal_year = db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            return jsonify({'error': '会計年度が見つかりません'}), 404
        
        # 企業情報を取得
        company = db.query(Company).filter(
            Company.id == fiscal_year.company_id,
            Company.tenant_id == tenant_id
        ).first()
        
        if not company:
            return jsonify({'error': '企業が見つかりません'}), 404
        
        # PLを取得
        pl = db.query(ProfitLossStatement).filter(
            ProfitLossStatement.fiscal_year_id == fiscal_year_id
        ).first()
        
        if not pl:
            return jsonify({'error': 'PLが見つかりません'}), 404
        
        # 簡易的に年間データを12ヶ月に均等配分
        monthly_sales = [float(pl.sales or 0) / 12] * 12
        monthly_cost_of_sales = [float(pl.cost_of_sales or 0) / 12] * 12
        monthly_operating_expenses = [float(pl.operating_expenses or 0) / 12] * 12
        
        # 営業CFを計算
        monthly_operating_cf = calculate_operating_cash_flow_from_pl(
            monthly_sales=monthly_sales,
            monthly_cost_of_sales=monthly_cost_of_sales,
            monthly_operating_expenses=monthly_operating_expenses
        )
        
        # 投資CFを計算（簡易的にゼロとする）
        monthly_investment_cf = calculate_investment_cash_flow_from_capex(
            monthly_capital_expenditure=[0] * 12
        )
        
        # 財務CFを計算（簡易的にゼロとする）
        monthly_financing_cf = calculate_financing_cash_flow_from_debt(
            monthly_borrowing=[0] * 12,
            monthly_debt_repayment=[0] * 12,
            monthly_interest_payment=[0] * 12
        )
        
        # 統合資金繰り表を生成
        result = generate_integrated_monthly_cash_flow(
            fiscal_year_id=fiscal_year_id,
            beginning_cash_balance=beginning_cash_balance,
            monthly_operating_cash_flow=monthly_operating_cf,
            monthly_investment_cash_flow=monthly_investment_cf,
            monthly_financing_cash_flow=monthly_financing_cf,
            minimum_cash_balance=minimum_cash_balance
        )
        
        # UI表示用に整形
        formatted_table = format_cash_flow_table_for_ui(result['cash_flow_table'])
        
        # 警告メッセージを生成
        alert_message = generate_shortage_alert_message(result['shortage_warnings'])
        
        # 資金調達提案を生成
        financing_solution = suggest_financing_solution(
            result['shortage_warnings'],
            available_credit_line=5000000  # 仮の与信枠
        )
        
        return jsonify({
            'success': True,
            'data': {
                'fiscal_year_id': result['fiscal_year_id'],
                'beginning_cash_balance': result['beginning_cash_balance'],
                'minimum_cash_balance': result['minimum_cash_balance'],
                'ending_cash_balance': result['ending_cash_balance'],
                'has_shortage': result['has_shortage'],
                'shortage_count': len(result['shortage_warnings']),
                'cash_flow_table': formatted_table,
                'shortage_warnings': result['shortage_warnings'],
                'alert_message': alert_message,
                'financing_solution': financing_solution
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/financing/amortization-schedule')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def amortization_schedule():
    """償却スケジュールを生成（UI表示用に整形）"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    principal = request.args.get('principal', type=float)
    annual_interest_rate = request.args.get('annual_interest_rate', type=float)
    term_years = request.args.get('term_years', type=int)
    payment_frequency = request.args.get('payment_frequency', type=str, default='monthly')
    
    if not principal or not annual_interest_rate or not term_years:
        return jsonify({'error': 'パラメータが不足しています'}), 400
    
    try:
        from ..utils.financing_repayment_planner import generate_amortization_schedule
        from ..utils.repayment_plan_formatter import format_amortization_schedule_for_ui
        
        # 償却スケジュールを生成
        schedule = generate_amortization_schedule(
            principal=principal,
            annual_interest_rate=annual_interest_rate,
            term_years=term_years,
            payment_frequency=payment_frequency
        )
        
        # UI表示用に整形
        formatted_schedule = format_amortization_schedule_for_ui(schedule, payment_frequency)
        
        return jsonify({
            'success': True,
            'data': formatted_schedule
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/financing/refinancing-comparison')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def refinancing_comparison():
    """借換え効果比較（UI表示用に整形）"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    current_loan_balance = request.args.get('current_loan_balance', type=float)
    current_interest_rate = request.args.get('current_interest_rate', type=float)
    remaining_term_years = request.args.get('remaining_term_years', type=int)
    new_interest_rate = request.args.get('new_interest_rate', type=float)
    refinancing_cost = request.args.get('refinancing_cost', type=float, default=0)
    
    if not current_loan_balance or not current_interest_rate or not remaining_term_years or not new_interest_rate:
        return jsonify({'error': 'パラメータが不足しています'}), 400
    
    try:
        from ..utils.financing_repayment_planner import calculate_refinancing_benefit
        from ..utils.repayment_plan_formatter import format_refinancing_comparison_for_ui
        
        # 借換え効果を計算
        result = calculate_refinancing_benefit(
            current_loan_balance=current_loan_balance,
            current_interest_rate=current_interest_rate,
            remaining_term_years=remaining_term_years,
            new_interest_rate=new_interest_rate,
            refinancing_cost=refinancing_cost
        )
        
        # UI表示用に整形
        formatted_result = format_refinancing_comparison_for_ui(result)
        
        return jsonify({
            'success': True,
            'data': formatted_result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/differential-analysis/equipment-investment')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def equipment_investment_differential_analysis():
    """設備投資の差額原価収益分析"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    equipment_cost = request.args.get('equipment_cost', type=float)
    useful_life = request.args.get('useful_life', type=int)
    current_labor_cost = request.args.get('current_labor_cost', type=float)
    new_labor_cost = request.args.get('new_labor_cost', type=float)
    tax_rate = request.args.get('tax_rate', type=float, default=30.0)
    discount_rate = request.args.get('discount_rate', type=float, default=6.0)
    
    if not equipment_cost or not useful_life or not current_labor_cost or not new_labor_cost:
        return jsonify({'error': 'パラメータが不足しています'}), 400
    
    try:
        from ..utils.equipment_investment_differential_analysis import (
            calculate_equipment_investment_differential_analysis,
            format_differential_analysis_for_ui
        )
        
        # 差額原価収益分析を実行
        result = calculate_equipment_investment_differential_analysis(
            equipment_cost=equipment_cost,
            useful_life=useful_life,
            current_labor_cost=current_labor_cost,
            new_labor_cost=new_labor_cost,
            tax_rate=tax_rate,
            discount_rate=discount_rate
        )
        
        # UI表示用に整形
        formatted_result = format_differential_analysis_for_ui(result)
        
        return jsonify({
            'success': True,
            'data': formatted_result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/differential-analysis/compare-equipment-investments', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def compare_equipment_investments():
    """複数の設備投資案を比較"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data or 'investment_plans' not in data:
        return jsonify({'error': 'investment_plansが必要です'}), 400
    
    investment_plans = data['investment_plans']
    tax_rate = data.get('tax_rate', 30.0)
    discount_rate = data.get('discount_rate', 6.0)
    
    try:
        from ..utils.equipment_investment_differential_analysis import (
            compare_multiple_equipment_investments,
            format_differential_analysis_for_ui
        )
        
        # 複数の投資案を比較
        result = compare_multiple_equipment_investments(
            investment_plans=investment_plans,
            tax_rate=tax_rate,
            discount_rate=discount_rate
        )
        
        # 各投資案をUI表示用に整形
        formatted_plans = []
        for plan in result['investment_plans']:
            formatted_plan = format_differential_analysis_for_ui(plan)
            formatted_plan['plan_name'] = plan['plan_name']
            formatted_plans.append(formatted_plan)
        
        return jsonify({
            'success': True,
            'data': {
                'investment_plans': formatted_plans,
                'best_plan_name': result['best_plan']['plan_name'] if result['best_plan'] else None,
                'comparison_summary': result['comparison_summary']
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/capital-investment/evaluate')
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def evaluate_capital_investment():
    """設備投資案件を総合評価"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    initial_investment = request.args.get('initial_investment', type=float)
    annual_cash_flows_str = request.args.get('annual_cash_flows', type=str)
    discount_rate = request.args.get('discount_rate', type=float, default=6.0)
    project_name = request.args.get('project_name', type=str, default='投資案件')
    
    if not initial_investment or not annual_cash_flows_str:
        return jsonify({'error': 'パラメータが不足しています'}), 400
    
    try:
        # カンマ区切りの文字列をリストに変換
        annual_cash_flows = [float(x.strip()) for x in annual_cash_flows_str.split(',')]
        
        from ..utils.capital_investment_planner import evaluate_investment
        
        # 設備投資案件を評価
        result = evaluate_investment(
            initial_investment=initial_investment,
            annual_cash_flows=annual_cash_flows,
            discount_rate=discount_rate,
            project_name=project_name
        )
        
        return jsonify({
            'success': True,
            'data': {
                'project_name': result['project_name'],
                'initial_investment': result['initial_investment'],
                'initial_investment_formatted': f"{result['initial_investment']:,.0f}円",
                'npv': round(result['npv'], 2),
                'npv_formatted': f"{result['npv']:,.0f}円",
                'irr': round(result['irr'], 2) if not (result['irr'] != result['irr']) else None,
                'irr_formatted': f"{result['irr']:.2f}%" if not (result['irr'] != result['irr']) else 'N/A',
                'payback_period': round(result['payback_period'], 2),
                'payback_period_formatted': f"{result['payback_period']:.1f}年",
                'profitability_index': round(result['profitability_index'], 2),
                'profitability_index_formatted': f"{result['profitability_index']:.2f}",
                'total_cash_flow': result['total_cash_flow'],
                'total_cash_flow_formatted': f"{result['total_cash_flow']:,.0f}円",
                'net_profit': result['net_profit'],
                'net_profit_formatted': f"{result['net_profit']:,.0f}円",
                'recommendation': result['recommendation']
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/contribution-analysis/product', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def product_contribution_analysis():
    """製品別貢献度分析"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data or 'products' not in data:
        return jsonify({'error': 'productsが必要です'}), 400
    
    products = data['products']
    
    try:
        from ..utils.product_contribution_analyzer import (
            analyze_product_contribution,
            format_product_contribution_for_ui,
            rank_products_by_contribution,
            identify_unprofitable_products
        )
        
        # 製品別貢献度分析を実行
        result = analyze_product_contribution(products)
        
        # UI表示用に整形
        formatted_result = format_product_contribution_for_ui(result)
        
        # ランキングを生成
        ranked_products = rank_products_by_contribution(result['products'])
        
        # 不採算製品を特定
        unprofitable_products = identify_unprofitable_products(result['products'])
        
        return jsonify({
            'success': True,
            'data': {
                'analysis': formatted_result,
                'ranking': [
                    {
                        'rank': i + 1,
                        'name': p['name'],
                        'contribution_profit': p['contribution_profit'],
                        'contribution_profit_formatted': f"{p['contribution_profit']:,.0f}円"
                    }
                    for i, p in enumerate(ranked_products)
                ],
                'unprofitable_products': [
                    {
                        'name': p['name'],
                        'contribution_profit': p['contribution_profit'],
                        'contribution_profit_formatted': f"{p['contribution_profit']:,.0f}円"
                    }
                    for p in unprofitable_products
                ]
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/contribution-analysis/segment', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def segment_contribution_analysis():
    """セグメント別貢献度分析"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data or 'segments' not in data:
        return jsonify({'error': 'segmentsが必要です'}), 400
    
    segments = data['segments']
    common_fixed_cost = data.get('common_fixed_cost', 0)
    
    try:
        from ..utils.contribution_analyzer import (
            analyze_product_mix,
            rank_segments_by_contribution,
            identify_unprofitable_segments
        )
        
        # セグメント別貢献度分析を実行
        result = analyze_product_mix(segments, common_fixed_cost)
        
        # ランキングを生成
        ranked_segments = rank_segments_by_contribution(result['segments'])
        
        # 不採算セグメントを特定
        unprofitable_segments = identify_unprofitable_segments(result['segments'])
        
        return jsonify({
            'success': True,
            'data': {
                'segments': result['segments'],
                'total': result['total'],
                'ranking': [
                    {
                        'rank': i + 1,
                        'name': s['name'],
                        'contribution_margin': s['contribution_margin'],
                        'contribution_margin_formatted': f"{s['contribution_margin']:,.0f}円"
                    }
                    for i, s in enumerate(ranked_segments)
                ],
                'unprofitable_segments': [
                    {
                        'name': s['name'],
                        'segment_profit': s['segment_profit'],
                        'segment_profit_formatted': f"{s['segment_profit']:,.0f}円"
                    }
                    for s in unprofitable_segments
                ]
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/budget-management/multi-year-plan', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def create_multi_year_plan():
    """多年度計画の作成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'データが必要です'}), 400
    
    try:
        from ..utils.multi_year_plan_manager import MultiYearPlanManager
        
        # 統合計画を作成
        integrated_plan = MultiYearPlanManager.create_integrated_plan(
            company_id=data.get('company_id'),
            base_year=data.get('base_year'),
            labor_cost_plans=data.get('labor_cost_plans', []),
            capital_investment_plans=data.get('capital_investment_plans', []),
            working_capital_plans=data.get('working_capital_plans', []),
            financing_plans=data.get('financing_plans', [])
        )
        
        # 計画の妥当性を検証
        validation_result = MultiYearPlanManager.validate_plan(integrated_plan)
        
        # UI表示用に整形
        formatted_plan = MultiYearPlanManager.format_plan_for_ui(integrated_plan)
        
        return jsonify({
            'success': True,
            'data': {
                'plan': formatted_plan,
                'validation': validation_result
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/budget-management/continuous-simulation', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def run_continuous_simulation():
    """連続財務シミュレーションの実行"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'データが必要です'}), 400
    
    try:
        from ..utils.continuous_financial_simulator import ContinuousFinancialSimulator
        
        # シミュレーションを実行
        simulation_result = ContinuousFinancialSimulator.simulate_multi_year_financials(
            base_financials=data.get('base_financials', {}),
            integrated_plan=data.get('integrated_plan', {}),
            sales_growth_rates=data.get('sales_growth_rates', []),
            cost_of_sales_ratios=data.get('cost_of_sales_ratios', []),
            sg_a_ratios=data.get('sg_a_ratios', [])
        )
        
        # UI表示用に整形
        formatted_result = ContinuousFinancialSimulator.format_simulation_for_ui(simulation_result)
        
        return jsonify({
            'success': True,
            'data': formatted_result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/budget-management/variance-analysis', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def analyze_budget_variance():
    """予実差異分析"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'データが必要です'}), 400
    
    try:
        from ..utils.budget_variance_analyzer import BudgetVarianceAnalyzer
        
        # 予実差異を分析
        variance_result = BudgetVarianceAnalyzer.analyze_variance(
            budget_data=data.get('budget_data', {}),
            actual_data=data.get('actual_data', {}),
            variance_threshold=data.get('variance_threshold', 5.0)
        )
        
        # UI表示用に整形
        formatted_result = BudgetVarianceAnalyzer.format_variance_for_ui(variance_result)
        
        return jsonify({
            'success': True,
            'data': formatted_result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/budget-management/alerts', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def generate_budget_alerts():
    """予算管理アラートの生成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'データが必要です'}), 400
    
    try:
        from ..utils.budget_variance_analyzer import BudgetVarianceAnalyzer
        
        # 包括的なアラートを生成
        alerts_result = BudgetVarianceAnalyzer.generate_comprehensive_alerts(
            budget_data=data.get('budget_data', {}),
            actual_data=data.get('actual_data', {}),
            simulation_result=data.get('simulation_result', {}),
            variance_threshold=data.get('variance_threshold', 5.0),
            minimum_cash_balance=data.get('minimum_cash_balance', 0),
            minimum_dscr=data.get('minimum_dscr', 1.2)
        )
        
        return jsonify({
            'success': True,
            'data': alerts_result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/individual-plans/labor-cost', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def create_multi_year_labor_cost_plan():
    """多年度労務費計画の作成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'データが必要です'}), 400
    
    try:
        from ..utils.multi_year_labor_cost_planner import (
            create_multi_year_labor_cost_plan,
            format_multi_year_labor_cost_plan_for_ui
        )
        
        # 多年度労務費計画を作成
        multi_year_plan = create_multi_year_labor_cost_plan(
            base_year=data.get('base_year'),
            current_employee_count=data.get('current_employee_count'),
            yearly_plans=data.get('yearly_plans', [])
        )
        
        # UI表示用に整形
        formatted_plan = format_multi_year_labor_cost_plan_for_ui(multi_year_plan)
        
        return jsonify({
            'success': True,
            'data': formatted_plan
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/individual-plans/capital-investment', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def create_multi_year_capital_investment_plan():
    """多年度設備投資計画の作成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'データが必要です'}), 400
    
    try:
        from ..utils.multi_year_capital_investment_planner import (
            create_multi_year_capital_investment_plan,
            format_multi_year_capital_investment_plan_for_ui
        )
        
        # 多年度設備投資計画を作成
        multi_year_plan = create_multi_year_capital_investment_plan(
            base_year=data.get('base_year'),
            yearly_investments=data.get('yearly_investments', [])
        )
        
        # UI表示用に整形
        formatted_plan = format_multi_year_capital_investment_plan_for_ui(multi_year_plan)
        
        return jsonify({
            'success': True,
            'data': formatted_plan
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/individual-plans/working-capital', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def create_multi_year_working_capital_plan():
    """多年度運転資金計画の作成"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return jsonify({'error': 'テナントIDが見つかりません'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'データが必要です'}), 400
    
    try:
        from ..utils.multi_year_working_capital_planner import (
            create_multi_year_working_capital_plan,
            format_multi_year_working_capital_plan_for_ui
        )
        
        # 多年度運転資金計画を作成
        multi_year_plan = create_multi_year_working_capital_plan(
            base_year=data.get('base_year'),
            yearly_plans=data.get('yearly_plans', [])
        )
        
        # UI表示用に整形
        formatted_plan = format_multi_year_working_capital_plan_for_ui(multi_year_plan)
        
        return jsonify({
            'success': True,
            'data': formatted_plan
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== PL組換え ====================

@bp.route('/pl-restructuring', methods=['GET', 'POST'])
@require_roles(ROLES['TENANT_ADMIN'], ROLES['SYSTEM_ADMIN'], ROLES['ADMIN'], ROLES['EMPLOYEE'])
def pl_restructuring():
    """PL組換え（損益計算書の組換え）"""
    import traceback as _traceback
    from ..models_decision import RestructuredPL
    db = SessionLocal()
    try:
        tenant_id = session.get('tenant_id')
        companies = db.query(Company).filter_by(tenant_id=tenant_id).all()

        company_id = request.args.get('company_id', type=int) or request.form.get('company_id', type=int)
        fiscal_year_id = request.args.get('fiscal_year_id', type=int) or request.form.get('fiscal_year_id', type=int)

        selected_company = None
        fiscal_years = []
        selected_fy = None
        rpl = None

        if company_id:
            selected_company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
            if selected_company:
                fiscal_years = db.query(FiscalYear).filter_by(company_id=company_id).order_by(FiscalYear.start_date.desc()).all()

        otb = None
        otb_pl_items = []
        if fiscal_year_id:
            selected_fy = db.query(FiscalYear).filter_by(id=fiscal_year_id).first()
            if selected_fy:
                rpl = db.query(RestructuredPL).filter_by(fiscal_year_id=fiscal_year_id).first()
                otb = db.query(OriginalTrialBalance).filter_by(fiscal_year_id=fiscal_year_id).first()
                if otb and otb.pl_items:
                    import json as json_module
                    try:
                        otb_pl_items = json_module.loads(otb.pl_items)
                        if not isinstance(otb_pl_items, list):
                            otb_pl_items = []
                    except (json_module.JSONDecodeError, ValueError):
                        otb_pl_items = []

        if request.method == 'POST':
            if not selected_fy:
                return redirect(url_for('decision.pl_restructuring'))

            def pi(key):
                return parse_int(request.form.get(key, '0') or '0')

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
            return redirect(url_for('decision.pl_restructuring', company_id=company_id, fiscal_year_id=fiscal_year_id))

        return render_template('pl_restructuring.html',
            companies=companies,
            selected_company=selected_company,
            fiscal_years=fiscal_years,
            selected_fy=selected_fy,
            rpl=rpl,
            otb_pl_items=otb_pl_items
        )
    except Exception as _e:
        db.rollback()
        _tb = _traceback.format_exc()
        return jsonify({'error': str(_e), 'traceback': _tb}), 500
    finally:
        db.close()
# ==================== BS組換え ======================

@bp.route('/bs-restructuring', methods=['GET', 'POST'])
@require_roles(ROLES['TENANT_ADMIN'], ROLES['SYSTEM_ADMIN'], ROLES['ADMIN'], ROLES['EMPLOYEE'])
def bs_restructuring():
    """BS組換え（貸借対照表の組換え）"""
    from ..models_decision import RestructuredBS
    db = SessionLocal()
    try:
        tenant_id = session.get('tenant_id')
        companies = db.query(Company).filter_by(tenant_id=tenant_id).all()

        company_id = request.args.get('company_id', type=int) or request.form.get('company_id', type=int)
        fiscal_year_id = request.args.get('fiscal_year_id', type=int) or request.form.get('fiscal_year_id', type=int)

        selected_company = None
        fiscal_years = []
        selected_fy = None
        rbs = None

        if company_id:
            selected_company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
            if selected_company:
                fiscal_years = db.query(FiscalYear).filter_by(company_id=company_id).order_by(FiscalYear.start_date.desc()).all()

        otb_bs_items = []
        if fiscal_year_id:
            selected_fy = db.query(FiscalYear).filter_by(id=fiscal_year_id).first()
            if selected_fy:
                rbs = db.query(RestructuredBS).filter_by(fiscal_year_id=fiscal_year_id).first()
                otb = db.query(OriginalTrialBalance).filter_by(fiscal_year_id=fiscal_year_id).first()
                if otb and otb.bs_items:
                    import json as json_module
                    try:
                        otb_bs_items = json_module.loads(otb.bs_items)
                        if not isinstance(otb_bs_items, list):
                            otb_bs_items = []
                    except (json_module.JSONDecodeError, ValueError):
                        otb_bs_items = []

        if request.method == 'POST':
            if not selected_fy:
                return redirect(url_for('decision.bs_restructuring'))

            def pi(key):
                return parse_int(request.form.get(key, '0') or '0')

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
            return redirect(url_for('decision.bs_restructuring', company_id=company_id, fiscal_year_id=fiscal_year_id))

        return render_template('bs_restructuring.html',
            companies=companies,
            selected_company=selected_company,
            fiscal_years=fiscal_years,
            selected_fy=selected_fy,
            rbs=rbs,
            otb_bs_items=otb_bs_items
        )
    finally:
        db.close()


## ==================== PDF財務諸表読み取り ====================
import os
import tempfile
from ..services.pdf_parser_service import parse_financial_pdf, reparse_with_instruction
from ..models_decision import RestructuredPL, RestructuredBS
from ..models_login import TKanrisha
@bp.route('/pdf-upload', methods=['GET', 'POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def pdf_upload():
    """PDF財務諸表アップロード・読み取りページ"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        companies = db.query(Company).filter_by(tenant_id=tenant_id).all()
        # DBに保存されたOpenAI APIキーを取得（ログイン中のユーザーのAPIキーを優先）
        openai_api_key = None
        current_user_id = session.get('user_id')
        if current_user_id:
            current_user = db.query(TKanrisha).filter(TKanrisha.id == current_user_id).first()
            if current_user and current_user.openai_api_key and current_user.openai_api_key.strip():
                openai_api_key = current_user.openai_api_key.strip()
        # ログイン中のユーザーにAPIキーがない場合は、他のシステム管理者のAPIキーを探す
        if not openai_api_key:
            sys_admin = db.query(TKanrisha).filter(
                TKanrisha.openai_api_key != None,
                TKanrisha.openai_api_key != ''
            ).first()
            if sys_admin and sys_admin.openai_api_key:
                openai_api_key = sys_admin.openai_api_key.strip()

        selected_company = None
        fiscal_years = []
        selected_fy = None
        parse_result = None
        error_message = None

        company_id = request.args.get('company_id', type=int) or request.form.get('company_id', type=int)
        fiscal_year_id = request.args.get('fiscal_year_id', type=int) or request.form.get('fiscal_year_id', type=int)

        if company_id:
            selected_company = db.query(Company).filter_by(id=company_id, tenant_id=tenant_id).first()
            if selected_company:
                fiscal_years = db.query(FiscalYear).filter_by(company_id=company_id).order_by(FiscalYear.start_date.desc()).all()

        if fiscal_year_id:
            selected_fy = db.query(FiscalYear).filter_by(id=fiscal_year_id).first()

        if request.method == 'POST':
            # AJAX非同期読み取りの結果をJSONで受け取る場合
            parse_result_json = request.form.get('parse_result_json', '')
            if parse_result_json:
                import json as _json
                try:
                    parse_result = _json.loads(parse_result_json)
                    if 'error' in parse_result:
                        error_message = parse_result['error']
                except Exception:
                    error_message = '読み取り結果の解析に失敗しました'
            elif 'pdf_file' in request.files:
                # 従来の同期処理（フォールバック）
                pdf_file = request.files['pdf_file']
                target_types = request.form.getlist('target_types')

                if not pdf_file or pdf_file.filename == '':
                    error_message = 'PDFファイルを選択してください。'
                elif not pdf_file.filename.lower().endswith('.pdf'):
                    error_message = 'PDFファイルのみアップロード可能です。'
                elif not fiscal_year_id:
                    error_message = '企業と会計年度を選択してください。'
                else:
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                        pdf_file.save(tmp.name)
                        tmp_path = tmp.name
                    try:
                        parse_result = parse_financial_pdf(
                            tmp_path,
                            target_types=target_types if target_types else None,
                            api_key=openai_api_key
                        )
                    finally:
                        os.unlink(tmp_path)

                    if 'error' in parse_result:
                        error_message = parse_result['error']

        return render_template(
            'pdf_upload.html',
            companies=companies,
            selected_company=selected_company,
            fiscal_years=fiscal_years,
            selected_fy=selected_fy,
            parse_result=parse_result,
            error_message=error_message,
            company_id=company_id,
            fiscal_year_id=fiscal_year_id
        )
    finally:
        db.close()


@bp.route('/pdf-apply', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def pdf_apply():
    """PDF解析結果をBS・PLデータとして保存する"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        fiscal_year_id = request.form.get('fiscal_year_id', type=int)
        company_id = request.form.get('company_id', type=int)
        apply_types = request.form.getlist('apply_types')

        if not fiscal_year_id:
            return jsonify({'error': '会計年度が指定されていません'}), 400

        def pi(name, default=0):
            val = request.form.get(name, '')
            try:
                return int(str(val).replace(',', '').replace('\u3000', '').strip()) if val else default
            except (ValueError, TypeError):
                return default

        # ============================================================
        # 損益計算書 生データ（RawProfitLossStatement）への upsert 保存
        # ============================================================
        if 'profit_loss' in apply_types:
            raw_pls = db.query(RawProfitLossStatement).filter_by(fiscal_year_id=fiscal_year_id).first()
            if not raw_pls:
                # レコードが存在しない場合は新規作成
                raw_pls = RawProfitLossStatement(fiscal_year_id=fiscal_year_id)
                db.add(raw_pls)
            # 全項目を上書き保存
            raw_pls.sales                          = pi('pl_sales')
            raw_pls.beginning_inventory            = pi('pl_beginning_inventory')
            raw_pls.manufacturing_cost             = pi('pl_manufacturing_cost')
            raw_pls.ending_inventory               = pi('pl_ending_inventory')
            raw_pls.cost_of_sales                  = pi('pl_cost_of_sales')
            raw_pls.gross_profit                   = pi('pl_gross_profit')
            raw_pls.labor_cost                     = pi('pl_labor_cost')
            raw_pls.executive_compensation         = pi('pl_executive_compensation')
            raw_pls.capital_regeneration_cost      = pi('pl_capital_regeneration_cost')
            raw_pls.research_development_expenses  = pi('pl_research_development_expenses')
            raw_pls.general_expenses               = pi('pl_general_expenses')
            raw_pls.general_expenses_fixed         = pi('pl_general_expenses_fixed')
            raw_pls.general_expenses_variable      = pi('pl_general_expenses_variable')
            raw_pls.selling_general_admin_expenses = pi('pl_selling_general_admin_expenses')
            raw_pls.operating_income               = pi('pl_operating_income')
            raw_pls.financial_profit_loss          = pi('pl_financial_profit_loss')
            raw_pls.other_non_operating            = pi('pl_other_non_operating')
            raw_pls.ordinary_income                = pi('pl_ordinary_income')
            raw_pls.extraordinary_profit_loss      = pi('pl_extraordinary_profit_loss')
            raw_pls.income_before_tax              = pi('pl_income_before_tax')
            raw_pls.income_taxes                   = pi('pl_income_taxes')
            raw_pls.net_income                     = pi('pl_net_income')
            raw_pls.dividend                       = pi('pl_dividend')
            raw_pls.retained_profit                = pi('pl_retained_profit')
            raw_pls.legal_reserve                  = pi('pl_legal_reserve')
            raw_pls.voluntary_reserve              = pi('pl_voluntary_reserve')
            raw_pls.retained_earnings_increase     = pi('pl_retained_earnings_increase')

        # ============================================================
        # 貸借対照表 生データ（RawBalanceSheet）への upsert 保存
        # ============================================================
        if 'balance_sheet' in apply_types:
            raw_bs = db.query(RawBalanceSheet).filter_by(fiscal_year_id=fiscal_year_id).first()
            if not raw_bs:
                # レコードが存在しない場合は新規作成
                raw_bs = RawBalanceSheet(fiscal_year_id=fiscal_year_id)
                db.add(raw_bs)
            # 全項目を上書き保存
            raw_bs.cash_on_hand                        = pi('bs_cash_on_hand')
            raw_bs.investment_deposits                 = pi('bs_investment_deposits')
            raw_bs.marketable_securities               = pi('bs_marketable_securities')
            raw_bs.trade_receivables                   = pi('bs_trade_receivables')
            raw_bs.inventory_assets                    = pi('bs_inventory_assets')
            raw_bs.current_assets                      = pi('bs_current_assets')
            raw_bs.tangible_fixed_assets               = pi('bs_tangible_fixed_assets')
            raw_bs.intangible_fixed_assets             = pi('bs_intangible_fixed_assets')
            raw_bs.investments_and_other               = pi('bs_investments_and_other')
            raw_bs.deferred_assets                     = pi('bs_deferred_assets')
            raw_bs.fixed_assets                        = pi('bs_fixed_assets')
            raw_bs.total_assets                        = pi('bs_total_assets')
            raw_bs.trade_payables                      = pi('bs_trade_payables')
            raw_bs.short_term_borrowings               = pi('bs_short_term_borrowings')
            raw_bs.current_portion_long_term           = pi('bs_current_portion_long_term')
            raw_bs.discounted_notes                    = pi('bs_discounted_notes')
            raw_bs.other_current_liabilities           = pi('bs_other_current_liabilities')
            raw_bs.current_liabilities                 = pi('bs_current_liabilities')
            raw_bs.long_term_borrowings                = pi('bs_long_term_borrowings')
            raw_bs.executive_borrowings                = pi('bs_executive_borrowings')
            raw_bs.retirement_benefit_liability        = pi('bs_retirement_benefit_liability')
            raw_bs.other_fixed_liabilities             = pi('bs_other_fixed_liabilities')
            raw_bs.fixed_liabilities                   = pi('bs_fixed_liabilities')
            raw_bs.total_liabilities                   = pi('bs_total_liabilities')
            raw_bs.capital                             = pi('bs_capital')
            raw_bs.capital_surplus                     = pi('bs_capital_surplus')
            raw_bs.retained_earnings                   = pi('bs_retained_earnings')
            raw_bs.legal_reserve_bs                    = pi('bs_legal_reserve_bs')
            raw_bs.voluntary_reserve_bs                = pi('bs_voluntary_reserve_bs')
            raw_bs.retained_earnings_carried           = pi('bs_retained_earnings_carried')
            raw_bs.treasury_stock                      = pi('bs_treasury_stock')
            raw_bs.net_assets                          = pi('bs_net_assets')
            raw_bs.total_liabilities_and_net_assets    = pi('bs_total_liabilities_and_net_assets')

        # ============================================================
        # 製造原価報告書 生データ（RawManufacturingCostReport）への upsert 保存
        # ============================================================
        if 'manufacturing_cost' in apply_types:
            raw_mcr = db.query(RawManufacturingCostReport).filter_by(fiscal_year_id=fiscal_year_id).first()
            if not raw_mcr:
                # レコードが存在しない場合は新規作成
                raw_mcr = RawManufacturingCostReport(fiscal_year_id=fiscal_year_id)
                db.add(raw_mcr)
            # 全項目を上書き保存
            raw_mcr.beginning_raw_material              = pi('mc_beginning_raw_material')
            raw_mcr.raw_material_purchase               = pi('mc_raw_material_purchase')
            raw_mcr.ending_raw_material                 = pi('mc_ending_raw_material')
            raw_mcr.material_cost                       = pi('mc_material_cost')
            raw_mcr.labor_cost_manufacturing            = pi('mc_labor_cost_manufacturing')
            raw_mcr.outsourcing_cost                    = pi('mc_outsourcing_cost')
            raw_mcr.freight_manufacturing               = pi('mc_freight_manufacturing')
            raw_mcr.meeting_cost_manufacturing          = pi('mc_meeting_cost_manufacturing')
            raw_mcr.travel_cost_manufacturing           = pi('mc_travel_cost_manufacturing')
            raw_mcr.communication_cost_manufacturing    = pi('mc_communication_cost_manufacturing')
            raw_mcr.supplies_manufacturing              = pi('mc_supplies_manufacturing')
            raw_mcr.vehicle_cost_manufacturing          = pi('mc_vehicle_cost_manufacturing')
            raw_mcr.rent_manufacturing                  = pi('mc_rent_manufacturing')
            raw_mcr.insurance_manufacturing             = pi('mc_insurance_manufacturing')
            raw_mcr.depreciation_manufacturing          = pi('mc_depreciation_manufacturing')
            raw_mcr.repair_cost_manufacturing           = pi('mc_repair_cost_manufacturing')
            raw_mcr.other_manufacturing_cost            = pi('mc_other_manufacturing_cost')
            raw_mcr.manufacturing_expenses_total        = pi('mc_manufacturing_expenses_total')
            raw_mcr.total_manufacturing_cost_current    = pi('mc_total_manufacturing_cost_current')
            raw_mcr.beginning_wip                       = pi('mc_beginning_wip')
            raw_mcr.ending_wip                          = pi('mc_ending_wip')
            raw_mcr.total_manufacturing_cost            = pi('mc_total_manufacturing_cost')

        # オリジナル試算表データの保存（生科目JSONをそのまま保存）
        import json as json_module
        otb_pl_items = request.form.get('otb_pl_items', '')
        otb_bs_items = request.form.get('otb_bs_items', '')
        otb_mcr_items = request.form.get('otb_mcr_items', '')
        otb_unit = request.form.get('otb_unit', '円')
        if otb_pl_items or otb_bs_items or otb_mcr_items:
            otb = db.query(OriginalTrialBalance).filter_by(fiscal_year_id=fiscal_year_id).first()
            if not otb:
                otb = OriginalTrialBalance(fiscal_year_id=fiscal_year_id)
                db.add(otb)
            if otb_pl_items:
                otb.pl_items = otb_pl_items
            if otb_bs_items:
                otb.bs_items = otb_bs_items
            if otb_mcr_items:
                otb.mcr_items = otb_mcr_items
            otb.unit = otb_unit

        # ============================================================
        # 勘定科目マスタ自動登録 + 財務諸表実績値保存
        # PDFから読み取った科目名が未登録の場合は新規追加し、金額を保存する
        # ============================================================
        if company_id:
            def upsert_statement_values(items_json, account_model, value_model, order_start=0):
                """JSON文字列から科目名・金額を取り出し、科目マスタ登録＋実績値upsertを行う"""
                if not items_json:
                    return
                try:
                    items = json_module.loads(items_json)
                except (ValueError, TypeError):
                    return
                if not isinstance(items, list):
                    return

                # 既存の科目マスタをname→idのdictで取得
                existing = {
                    row.account_name: row.id
                    for row in db.query(account_model)
                        .filter_by(tenant_id=tenant_id)
                        .all()
                }

                for order_idx, item in enumerate(items):
                    if not isinstance(item, dict):
                        continue
                    # 科目名キーは 'name' または 'account_name' を想定
                    account_name = item.get('name') or item.get('account_name') or ''
                    account_name = str(account_name).strip()
                    if not account_name:
                        continue

                    # 会計システムの大分類・中分類・小分類名と完全一致する項目は区分名なので科目マスタに登録しない
                    _ACCOUNT_SECTION_NAMES = {
                        # 大分類（科目名として使われない純粋な区分名のみ）
                        '資産', '負債', '純資産', '損益', '収益', '費用', '口座',
                        # 中分類（科目名として使われない純粋な区分名のみ）
                        '流動資産', '固定資産', '繰延資産',
                        '流動負債', '固定負債',
                        '資本剰余金', '利益剰余金', '自己株式', '評価換算差額等', '新株予約権',
                        '販売費及び一般管理費',
                        # 小分類（科目名として使われない純粋な区分名のみ）
                        '現金及び預金', '売上債権', '棚卸資産', '有価証券', '投資その他の資産',
                        '有形固定資産', '無形固定資産',
                        '仕入債務', 'その他流動負債', 'その他流動資産',
                        # その他純粋な区分名
                        '販管費',
                    }
                    if account_name in _ACCOUNT_SECTION_NAMES:
                        continue
                    # 金額取得
                    raw_amount = item.get('amount') or item.get('value') or 0
                    try:
                        amount = int(str(raw_amount).replace(',', '').replace('\u3000', '').strip())
                    except (ValueError, TypeError):
                        amount = 0

                    # PDFのセクション名から大分類・中分類・小分類へのマッピングテーブル
                    _SECTION_TO_CATEGORY = {
                        # BS - 資産
                        '流動資産':            ('資産', '流動資産', 'その他流動資産'),
                        '現金及び預金':          ('資産', '流動資産', '現金及び預金'),
                        '現金・預金':            ('資産', '流動資産', '現金及び預金'),
                        '売上債権':              ('資産', '流動資産', '売上債権'),
                        '棚卸資産':              ('資産', '流動資産', '棚卸資産'),
                        '有価証券':              ('資産', '流動資産', '有価証券'),
                        'その他流動資産':          ('資産', '流動資産', 'その他流動資産'),
                        '固定資産':            ('資産', '固定資産', 'その他流動資産'),
                        '有形固定資産':          ('資産', '固定資産', '有形固定資産'),
                        '無形固定資産':          ('資産', '固定資産', '無形固定資産'),
                        '投資その他の資産':        ('資産', '固定資産', '投資その他の資産'),
                        '繰延資産':            ('資産', '繰延資産', '繰延資産'),
                        # BS - 負債
                        '流動負債':            ('負債', '流動負債', 'その他流動負債'),
                        '仕入債務':              ('負債', '流動負債', '仕入債務'),
                        'その他流動負債':          ('負債', '流動負債', 'その他流動負債'),
                        '固定負債':            ('負債', '固定負債', '固定負債'),
                        # BS - 純資産
                        '純資産':              ('純資産', '資本金', '資本金'),
                        '資本金':              ('純資産', '資本金', '資本金'),
                        '資本剰余金':            ('純資産', '資本剰余金', 'その他資本剰余金'),
                        '利益剰余金':            ('純資産', '利益剰余金', 'その他利益剰余金'),
                        '自己株式':              ('純資産', '自己株式', '自己株式'),
                        # PL - 損益
                        '売上高':              ('損益', '売上高', '売上高'),
                        '売上原価':            ('損益', '売上原価', '売上原価'),
                        '販売費及び一般管理費':    ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
                        '販管費':              ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
                        '販売費':              ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
                        '一般管理費':            ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
                        '営業外収益':            ('損益', '営業外収益', '営業外収益'),
                        '営業外費用':            ('損益', '営業外費用', '営業外費用'),
                        '特別利益':            ('損益', '特別利益', '特別利益'),
                        '特別損失':            ('損益', '特別損失', '特別損失'),
                        '法人税等':              ('損益', '法人税等', '法人税等'),
                        # MCR
                        '製造原価':            ('損益', '売上原価', '売上原価'),
                        '材料費':              ('損益', '売上原価', '売上原価'),
                        '労務費':              ('損益', '売上原価', '売上原価'),
                        '製造経費':            ('損益', '売上原価', '売上原価'),
                    }

                    # 科目マスタに未登録なら新規追加
                    if account_name not in existing:
                        # PDFのセクション名から大中小分類を取得
                        section = item.get('section', '')
                        cat = _SECTION_TO_CATEGORY.get(section)
                        new_item = account_model(
                            tenant_id=tenant_id,
                            account_name=account_name,
                            display_order=order_start + order_idx,
                            is_auto_created=True,
                            major_category=cat[0] if cat else None,
                            mid_category=cat[1] if cat else None,
                            sub_category=cat[2] if cat else None,
                            category_status='confirmed' if cat else 'uncategorized',
                        )
                        db.add(new_item)
                        db.flush()  # IDを確定させる
                        existing[account_name] = new_item.id
                    else:
                        # 既存科目は最新PDFの表示順に同期し、未分類ならセクション情報で更新
                        section = item.get('section', '')
                        cat = _SECTION_TO_CATEGORY.get(section)
                        existing_item = db.query(account_model).filter_by(
                            tenant_id=tenant_id, account_name=account_name
                        ).first()
                        if existing_item:
                            existing_item.display_order = order_start + order_idx
                            if cat and existing_item.category_status in ('uncategorized', None):
                                existing_item.major_category = cat[0]
                                existing_item.mid_category = cat[1]
                                existing_item.sub_category = cat[2]
                                existing_item.category_status = 'confirmed'

                    account_item_id = existing[account_name]

                    # 実績値をupsert（既存なら更新、なければ新規）
                    sv = db.query(value_model).filter_by(
                        fiscal_year_id=fiscal_year_id,
                        account_item_id=account_item_id
                    ).first()
                    if sv:
                        sv.amount = amount
                    else:
                        sv = value_model(
                            fiscal_year_id=fiscal_year_id,
                            account_item_id=account_item_id,
                            amount=amount
                        )
                        db.add(sv)

            upsert_statement_values(otb_pl_items,  PlAccountItem,  PlStatementValue,  order_start=0)
            upsert_statement_values(otb_bs_items,  BsAccountItem,  BsStatementValue,  order_start=0)
            upsert_statement_values(otb_mcr_items, McrAccountItem, McrStatementValue, order_start=0)

        db.commit()

        # ============================================================
        # AIマッピング推定（unmapped科目のみ対象）
        # ============================================================
        if company_id:
            try:
                from ..services.mapping_service import (
                    estimate_mappings_for_pl,
                    estimate_mappings_for_bs,
                    estimate_mappings_for_mcr,
                    estimate_categories
                )
                db2 = SessionLocal()
                try:
                    # PLの未マッピング科目を推定
                    pl_items_all = db2.query(PlAccountItem).filter_by(tenant_id=tenant_id).all()
                    pl_results = estimate_mappings_for_pl(tenant_id, pl_items_all)
                    for r in pl_results:
                        item = db2.query(PlAccountItem).get(r.get('id'))
                        if item and item.mapping_status in ('unmapped', None):
                            item.target_statement = r.get('target_statement')
                            item.target_field = r.get('target_field') if r.get('target_field') else None
                            item.ai_confidence = r.get('confidence')
                            item.mapping_status = 'pending'

                    # BSの未マッピング科目を推定
                    bs_items_all = db2.query(BsAccountItem).filter_by(tenant_id=tenant_id).all()
                    bs_results = estimate_mappings_for_bs(tenant_id, bs_items_all)
                    for r in bs_results:
                        item = db2.query(BsAccountItem).get(r.get('id'))
                        if item and item.mapping_status in ('unmapped', None):
                            item.target_statement = r.get('target_statement')
                            item.target_field = r.get('target_field') if r.get('target_field') else None
                            item.ai_confidence = r.get('confidence')
                            item.mapping_status = 'pending'

                    # MCRの未マッピング科目を推定
                    mcr_items_all = db2.query(McrAccountItem).filter_by(tenant_id=tenant_id).all()
                    mcr_results = estimate_mappings_for_mcr(tenant_id, mcr_items_all)
                    for r in mcr_results:
                        item = db2.query(McrAccountItem).get(r.get('id'))
                        if item and item.mapping_status in ('unmapped', None):
                            item.target_statement = r.get('target_statement')
                            item.target_field = r.get('target_field') if r.get('target_field') else None
                            item.ai_confidence = r.get('confidence')
                            item.mapping_status = 'pending'

                    # 分類推定（uncategorized科目のみ対象）
                    pl_cat_results = estimate_categories(pl_items_all, 'PL')
                    for r in pl_cat_results:
                        item = db2.query(PlAccountItem).get(r.get('id'))
                        if item and item.category_status in ('uncategorized', None):
                            item.major_category = r.get('major_category')
                            item.mid_category = r.get('mid_category')
                            item.sub_category = r.get('sub_category')
                            item.category_status = 'pending'

                    bs_cat_results = estimate_categories(bs_items_all, 'BS')
                    for r in bs_cat_results:
                        item = db2.query(BsAccountItem).get(r.get('id'))
                        if item and item.category_status in ('uncategorized', None):
                            item.major_category = r.get('major_category')
                            item.mid_category = r.get('mid_category')
                            item.sub_category = r.get('sub_category')
                            item.category_status = 'pending'

                    mcr_cat_results = estimate_categories(mcr_items_all, 'MCR')
                    for r in mcr_cat_results:
                        item = db2.query(McrAccountItem).get(r.get('id'))
                        if item and item.category_status in ('uncategorized', None):
                            item.major_category = r.get('major_category')
                            item.mid_category = r.get('mid_category')
                            item.sub_category = r.get('sub_category')
                            item.category_status = 'pending'

                    db2.commit()
                finally:
                    db2.close()
            except Exception as e:
                print(f'[pdf_apply] AI mapping error (non-fatal): {e}')

            # 勘定科目マスタ画面へリダイレクト
            return redirect(url_for('decision.account_master'))
        else:
            return redirect(url_for('decision.profit_loss_list'))
    finally:
        db.close()


# ==================== PDF非同期読み取り（AJAX） ====================
import threading
import uuid

# ジョブ管理（メモリ内）
_pdf_jobs = {}  # {job_id: {'status': 'pending'|'running'|'done'|'error', 'result': ..., 'error': ...}}
_pdf_jobs_lock = threading.Lock()


@bp.route('/pdf-parse-async', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def pdf_parse_async():
    """PDFをバックグラウンドで非同期読み取り開始"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        # APIキー取得
        openai_api_key = None
        current_user_id = session.get('user_id')
        if current_user_id:
            current_user = db.query(TKanrisha).filter(TKanrisha.id == current_user_id).first()
            if current_user and current_user.openai_api_key and current_user.openai_api_key.strip():
                openai_api_key = current_user.openai_api_key.strip()
        if not openai_api_key:
            sys_admin = db.query(TKanrisha).filter(
                TKanrisha.openai_api_key != None,
                TKanrisha.openai_api_key != ''
            ).first()
            if sys_admin and sys_admin.openai_api_key:
                openai_api_key = sys_admin.openai_api_key.strip()
    finally:
        db.close()

    if not openai_api_key:
        return jsonify({'error': 'OpenAI APIキーが設定されていません'}), 400

    pdf_file = request.files.get('pdf_file')
    if not pdf_file or pdf_file.filename == '':
        return jsonify({'error': 'PDFファイルを選択してください'}), 400
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'PDFファイルのみアップロード可能です'}), 400

    target_types = request.form.getlist('target_types')

    # 一時ファイルに保存
    tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    pdf_file.save(tmp.name)
    tmp_path = tmp.name
    tmp.close()

    # ジョブID生成
    job_id = str(uuid.uuid4())
    with _pdf_jobs_lock:
        _pdf_jobs[job_id] = {'status': 'running', 'result': None, 'error': None}

    def run_parse():
        try:
            result = parse_financial_pdf(
                tmp_path,
                target_types=target_types if target_types else None,
                api_key=openai_api_key
            )
            with _pdf_jobs_lock:
                _pdf_jobs[job_id]['status'] = 'done'
                _pdf_jobs[job_id]['result'] = result
        except Exception as e:
            with _pdf_jobs_lock:
                _pdf_jobs[job_id]['status'] = 'error'
                _pdf_jobs[job_id]['error'] = str(e)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    t = threading.Thread(target=run_parse, daemon=True)
    t.start()

    return jsonify({'job_id': job_id})


@bp.route('/pdf-reparse-async', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def pdf_reparse_async():
    """追加指示付きでPDF生科目データを再読み取り（非同期）"""
    import json as _json
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        openai_api_key = None
        current_user_id = session.get('user_id')
        if current_user_id:
            current_user = db.query(TKanrisha).filter(TKanrisha.id == current_user_id).first()
            if current_user and current_user.openai_api_key and current_user.openai_api_key.strip():
                openai_api_key = current_user.openai_api_key.strip()
        if not openai_api_key:
            sys_admin = db.query(TKanrisha).filter(
                TKanrisha.openai_api_key != None,
                TKanrisha.openai_api_key != ''
            ).first()
            if sys_admin and sys_admin.openai_api_key:
                openai_api_key = sys_admin.openai_api_key.strip()
    finally:
        db.close()

    if not openai_api_key:
        return jsonify({'error': 'OpenAI APIキーが設定されていません'}), 400

    additional_instruction = request.form.get('additional_instruction', '').strip()
    if not additional_instruction:
        return jsonify({'error': '追加指示を入力してください'}), 400

    raw_text = request.form.get('raw_text', '')
    current_items_json = request.form.get('current_items', '{}')
    try:
        current_items = _json.loads(current_items_json)
    except Exception:
        current_items = {}

    job_id = str(uuid.uuid4())
    with _pdf_jobs_lock:
        _pdf_jobs[job_id] = {'status': 'running', 'result': None, 'error': None}

    def run_reparse():
        try:
            result = reparse_with_instruction(
                pdf_text=raw_text,
                current_items=current_items,
                additional_instruction=additional_instruction,
                api_key=openai_api_key
            )
            with _pdf_jobs_lock:
                _pdf_jobs[job_id]['status'] = 'done'
                _pdf_jobs[job_id]['result'] = result
        except Exception as e:
            with _pdf_jobs_lock:
                _pdf_jobs[job_id]['status'] = 'error'
                _pdf_jobs[job_id]['error'] = str(e)

    t = threading.Thread(target=run_reparse, daemon=True)
    t.start()
    return jsonify({'job_id': job_id})


@bp.route('/pdf-parse-status/<job_id>', methods=['GET'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def pdf_parse_status(job_id):
    """PDF非同期読み取りの進捗確認"""
    with _pdf_jobs_lock:
        job = _pdf_jobs.get(job_id)
    if not job:
        return jsonify({'status': 'not_found'}), 404
    if job['status'] == 'done':
        result = job['result']
        # ジョブをメモリから削除（取得後）
        with _pdf_jobs_lock:
            _pdf_jobs.pop(job_id, None)
        return jsonify({'status': 'done', 'result': result})
    elif job['status'] == 'error':
        error = job['error']
        with _pdf_jobs_lock:
            _pdf_jobs.pop(job_id, None)
        return jsonify({'status': 'error', 'error': error})
    else:
        return jsonify({'status': 'running'})



# ==================== マイグレーション（Raw詳細テーブル作成） ====================

@bp.route('/run-migration-raw-tables', methods=['GET'])
def run_migration_raw_tables():
    """raw_profit_loss_statements / raw_balance_sheets / raw_manufacturing_cost_reports テーブルを作成し、
    StatementType ENUM に MCR を追加するマイグレーション"""
    from ..db import engine, Base
    from .. import models_decision  # noqa: F401 - 全モデルをBaseに登録
    from sqlalchemy import text

    results = []

    # 1. 新テーブルを create_all で作成（既存テーブルはスキップ）
    try:
        Base.metadata.create_all(bind=engine)
        results.append('create_all: OK')
    except Exception as e:
        results.append(f'create_all: ERROR - {e}')

    # 2. account_mappings の statement_type ENUM に MCR を追加（PostgreSQL用）
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TYPE statementtype ADD VALUE IF NOT EXISTS 'MCR'"))
            conn.commit()
        results.append('ALTER TYPE statementtype ADD VALUE MCR: OK')
    except Exception as e:
        results.append(f'ALTER TYPE statementtype: {e}')

    # 3. pl/bs/mcr_account_items にマッピングカラムを追加（既存テーブルへのALTER TABLE）
    mapping_columns = [
        ('pl_account_items',  'target_statement', 'VARCHAR(10)'),
        ('pl_account_items',  'target_field',     'VARCHAR(100)'),
        ('pl_account_items',  'mapping_status',   "VARCHAR(20) NOT NULL DEFAULT 'unmapped'"),
        ('pl_account_items',  'ai_confidence',    'FLOAT'),
        ('bs_account_items',  'target_statement', 'VARCHAR(10)'),
        ('bs_account_items',  'target_field',     'VARCHAR(100)'),
        ('bs_account_items',  'mapping_status',   "VARCHAR(20) NOT NULL DEFAULT 'unmapped'"),
        ('bs_account_items',  'ai_confidence',    'FLOAT'),
        ('mcr_account_items', 'target_statement', 'VARCHAR(10)'),
        ('mcr_account_items', 'target_field',     'VARCHAR(100)'),
        ('mcr_account_items', 'mapping_status',   "VARCHAR(20) NOT NULL DEFAULT 'unmapped'"),
        ('mcr_account_items', 'ai_confidence',    'FLOAT'),
    ]
    for table, col, col_type in mapping_columns:
        try:
            with engine.connect() as conn:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}'))
                conn.commit()
            results.append(f'ALTER TABLE {table} ADD COLUMN {col}: OK')
        except Exception as e:
            results.append(f'ALTER TABLE {table} ADD COLUMN {col}: {e}')

    return {'results': results}, 200


# ==================== マッピング確認・確定 ====================

# 組換え先フィールドの選択肢定義
_PL_FIELDS = {
    'sales': '1. 売上高',
    'cost_of_sales': '2. 売上原価（合計）',
    'beginning_inventory': '（1）期首棚卸高',
    'manufacturing_cost': '（2）当期製造（工事）原価',
    'ending_inventory': '（3）期末棚卸高',
    'gross_profit': '売上総利益',
    'external_cost_adjustment': '5. 外部経費調整',
    'gross_added_value': '6. 粗付加価値',
    'selling_general_admin_expenses': '3. 販売費及び一般管理費（合計）',
    'labor_cost': '（1）人件費',
    'executive_compensation': '（2）役員報酬',
    'capital_regeneration_cost': '（3）資本再生費',
    'research_development_expenses': '（4）研究開発費',
    'general_expenses': '（5）一般経費',
    'general_expenses_fixed': '① 固定費',
    'general_expenses_variable': '② 変動費',
    'operating_income': '営業利益',
    'financial_profit_loss': '4. 金融損益',
    'other_non_operating': 'その他営業外損益',
    'ordinary_income': '経常利益',
    'extraordinary_profit_loss': '5. 特別損益',
    'income_before_tax': '税引前当期純利益',
    'income_taxes': '法人税・住民税・事業税',
    'net_income': '当期純利益',
    'dividend': '（1）配当金',
    'retained_profit': '（2）内部留保',
    'legal_reserve': '① 利益準備金積立額',
    'voluntary_reserve': '② その他剰余金積立額',
    'retained_earnings_increase': '③ 繰越利益剰余金増加',
}

_PL_FIELD_GROUPS = [
    {'label': '1. 売上高', 'options': ['sales']},
    {'label': '2. 売上原価', 'options': ['beginning_inventory', 'manufacturing_cost', 'ending_inventory', 'cost_of_sales']},
    {'label': '売上総利益・付加価値', 'options': ['gross_profit', 'external_cost_adjustment', 'gross_added_value']},
    {'label': '3. 販売費及び一般管理費', 'options': ['labor_cost', 'executive_compensation', 'capital_regeneration_cost', 'research_development_expenses', 'general_expenses', 'general_expenses_fixed', 'general_expenses_variable', 'selling_general_admin_expenses']},
    {'label': '4. 営業外損益', 'options': ['operating_income', 'financial_profit_loss', 'other_non_operating', 'ordinary_income']},
    {'label': '5. 特別損益・税金', 'options': ['extraordinary_profit_loss', 'income_before_tax', 'income_taxes', 'net_income']},
    {'label': '6. 利益処分', 'options': ['dividend', 'retained_profit', 'legal_reserve', 'voluntary_reserve', 'retained_earnings_increase']},
]

_BS_FIELDS = {
    'cash_on_hand': '① 手許現預金',
    'investment_deposits': '② 運用預金',
    'marketable_securities': '③ 有価証券',
    'other_current_assets': '④ その他（流動資産）',
    'trade_receivables': '売掛債権',
    'inventory_assets': '棚卸資産',
    'land': '(1) 土地',
    'buildings_and_attached_facilities': '(2) 建物・附属設備等',
    'machinery_and_equipment': '(3) 機械装置',
    'vehicles_and_transport_equipment': '(4) 車輌運搬具',
    'tools_furniture_and_fixtures': '(5) 工具・器具・備品',
    'other_tangible_fixed_assets': '(6) その他（有形固定資産）',
    'tangible_fixed_assets': '有形固定資産（合計）',
    'intangible_fixed_assets': '無形固定資産',
    'investments_and_other': '投資その他の資産',
    'deferred_assets': '繰延資産',
    'trade_payables': '(1) 買掛債務',
    'short_term_borrowings': '(2) 短期借入金',
    'current_portion_long_term': '長期借入金（1年以内支払い）',
    'discounted_notes': '(3) 割引手形',
    'income_taxes_payable': '(4) 未払法人税等',
    'bonus_reserve': '(5) 賞与引当金',
    'other_allowances': '(6) その他引当金',
    'other_current_liabilities': '(7) その他',
    'long_term_borrowings': '(1) 長期借入金',
    'executive_borrowings': '(2) 役員等借入金',
    'retirement_benefit_liability': '(3) 退職給付引当金',
    'other_fixed_liabilities': '(4) その他',
    'capital': '資本金',
    'capital_reserve': '資本準備金',
    'other_capital_surplus': 'その他資本剰余金',
    'capital_surplus': '資本剰余金（合計）',
    'legal_reserve_bs': '利益準備金',
    'voluntary_reserve_bs': '任意積立金',
    'retained_earnings_carried': '繰越利益剰余金',
    'retained_earnings': '利益剰余金（合計）',
    'valuation_and_translation_adjustments': 'IV 評価・換算差額等',
    'treasury_stock': 'V 自己株式',
    'current_assets': '流動資産合計',
    'fixed_assets': '固定資産合計',
    'total_assets': '資産合計',
    'current_liabilities': '流動負債合計',
    'fixed_liabilities': '固定負債合計',
    'total_liabilities': '負債合計',
    'net_assets': '純資産合計',
    'total_liabilities_and_net_assets': '負債・純資産合計',
}

_BS_FIELD_GROUPS = [
    {'label': '資産の部 / 1. 当座資産', 'options': ['cash_on_hand', 'investment_deposits', 'marketable_securities']},
    {'label': '資産の部 / 2. 売掛債権', 'options': ['trade_receivables']},
    {'label': '資産の部 / 3. 棚卸資産', 'options': ['inventory_assets']},
    {'label': '資産の部 / 4. その他流動資産', 'options': ['other_current_assets']},
    {'label': '資産の部 / 固定資産 / 1. 有形固定資産', 'options': ['land', 'buildings_and_attached_facilities', 'machinery_and_equipment', 'vehicles_and_transport_equipment', 'tools_furniture_and_fixtures', 'other_tangible_fixed_assets', 'tangible_fixed_assets']},
    {'label': '資産の部 / 固定資産 / 2. 無形固定資産', 'options': ['intangible_fixed_assets']},
    {'label': '資産の部 / 固定資産 / 3. 投資その他の資産', 'options': ['investments_and_other']},
    {'label': '資産の部 / III. 繰延資産', 'options': ['deferred_assets']},
    {'label': '負債の部 / 4. 買掛債務', 'options': ['trade_payables']},
    {'label': '負債の部 / 5. 短期借入金・手形債務', 'options': ['short_term_borrowings', 'current_portion_long_term', 'discounted_notes']},
    {'label': '負債の部 / 6. その他流動負債・引当金', 'options': ['income_taxes_payable', 'bonus_reserve', 'other_allowances', 'other_current_liabilities']},
    {'label': '負債の部 / 固定負債', 'options': ['long_term_borrowings', 'executive_borrowings', 'retirement_benefit_liability', 'other_fixed_liabilities']},
    {'label': '純資産の部 / 1. 資本金', 'options': ['capital']},
    {'label': '純資産の部 / 2. 資本剰余金', 'options': ['capital_reserve', 'other_capital_surplus', 'capital_surplus']},
    {'label': '純資産の部 / 3. 利益剰余金', 'options': ['legal_reserve_bs', 'voluntary_reserve_bs', 'retained_earnings_carried', 'retained_earnings']},
    {'label': '純資産の部 / IV. 評価・換算差額等', 'options': ['valuation_and_translation_adjustments']},
    {'label': '純資産の部 / V. 自己株式', 'options': ['treasury_stock']},
    {'label': '参考：合計項目', 'options': ['current_assets', 'tangible_fixed_assets', 'fixed_assets', 'total_assets', 'current_liabilities', 'fixed_liabilities', 'total_liabilities', 'net_assets', 'total_liabilities_and_net_assets']},
]

_MCR_FIELDS = {
    'beginning_raw_material': '期首原材料棚卸高',
    'raw_material_purchase': '当期原材料仕入高',
    'ending_raw_material': '期末原材料棚卸高',
    'material_cost': '材料費計',
    'labor_cost_manufacturing': '労務費計',
    'outsourcing_cost': '外注加工費',
    'freight_manufacturing': '荷造運賃（製造）',
    'meeting_cost_manufacturing': '会議費（製造）',
    'travel_cost_manufacturing': '旅費交通費（製造）',
    'communication_cost_manufacturing': '通信費（製造）',
    'supplies_manufacturing': '消耗品費（製造）',
    'vehicle_cost_manufacturing': '車両費（製造）',
    'rent_manufacturing': '賃借料（製造）',
    'insurance_manufacturing': '保険料（製造）',
    'depreciation_manufacturing': '減価償却費（製造）',
    'repair_cost_manufacturing': '修繕費（製造）',
    'other_manufacturing_cost': 'その他製造経費',
    'manufacturing_expenses_total': '製造経費計',
    'total_manufacturing_cost_current': '総製造費用',
    'beginning_wip': '期首仕掛品棚卸高',
    'ending_wip': '期末仕掛品棚卸高',
    'total_manufacturing_cost': '製造原価合計',
}

_MCR_FIELD_GROUPS = [
    {'label': '1. 材料費', 'options': ['beginning_raw_material', 'raw_material_purchase', 'ending_raw_material', 'material_cost']},
    {'label': '2. 労務費', 'options': ['labor_cost_manufacturing']},
    {'label': '3. 製造経費', 'options': ['outsourcing_cost', 'freight_manufacturing', 'meeting_cost_manufacturing', 'travel_cost_manufacturing', 'communication_cost_manufacturing', 'supplies_manufacturing', 'vehicle_cost_manufacturing', 'rent_manufacturing', 'insurance_manufacturing', 'depreciation_manufacturing', 'repair_cost_manufacturing', 'other_manufacturing_cost', 'manufacturing_expenses_total']},
    {'label': '4. 総製造費用・仕掛品・製造原価', 'options': ['total_manufacturing_cost_current', 'beginning_wip', 'ending_wip', 'total_manufacturing_cost']},
]

_ALL_FIELDS = {
    'PL': _PL_FIELDS,
    'BS': _BS_FIELDS,
    'MCR': _MCR_FIELDS,
}

_FIXED_SUMMARY_ACCOUNT_NAMES = {
    '売上高計', '売上原価', '当期商品仕入', '商品売上原価', '当期製品製造原価', '製品売上原価',
    '売上総利益', '販売管理費計', '営業利益', '営業外収益', '営業外費用', '経常利益',
    '特別利益', '特別損失', '税引前当期純利益', '法人税等', '当期純利益',
    '期首原材料棚卸', '当期原材料仕入高', '期末原材料棚卸',
    '材料費計', '材料費系', '労務費計', '製造経費計', '総製造費用', '製造原価',
    '流動資産合計', '有形固定資産合計', '無形固定資産合計', '投資その他の資産合計', '固定資産合計',
    '資産合計', '流動負債合計', '固定負債合計', '負債合計', '資本金合計', '当期純損益金額',
    'その他利益剰余金合計', '利益剰余金合計', '自己株式合計', '株主資本合計', '評価・換算差額等合計',
    '新株予約権合計', '純資産合計', '負債及び純資産合計'
}


def _normalize_account_name(account_name):
    return str(account_name or '').replace(' ', '').replace('\u3000', '').strip()


_FIXED_SUMMARY_ACCOUNT_NAMES_NORMALIZED = {
    _normalize_account_name(name) for name in _FIXED_SUMMARY_ACCOUNT_NAMES
}


def _is_fixed_summary_account(account_name):
    return _normalize_account_name(account_name) in _FIXED_SUMMARY_ACCOUNT_NAMES_NORMALIZED

# ============================================================
# 科目マスタ管理画面
# ============================================================

@bp.route('/account-master', methods=['GET'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def account_master():
    """勘定科目マスタ管理画面（GET）"""
    import json, os
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        # 分類ツリーを読み込む
        cat_json_path = os.path.join(os.path.dirname(__file__), 'account_item_categories.json')
        with open(cat_json_path, 'r', encoding='utf-8') as f:
            category_tree = json.load(f)
        # PL/BS/MCR別にカテゴリツリーを分離
        _PL_MAJOR_KEYS = {'損益'}
        _BS_MAJOR_KEYS = {'資産', '負債', '純資産'}
        _MCR_MAJOR_KEYS = {'製造費用', '製造原価'}
        pl_category_tree = {k: v for k, v in category_tree.items() if k in _PL_MAJOR_KEYS}
        bs_category_tree = {k: v for k, v in category_tree.items() if k in _BS_MAJOR_KEYS}
        mcr_category_tree = {k: v for k, v in category_tree.items() if k in _MCR_MAJOR_KEYS}

        _ACCOUNT_SECTION_NAMES = {
            '資産', '負債', '純資産', '損益', '収益', '費用', '口座',
            '流動資産', '固定資産', '繰延資産',
            '流動負債', '固定負債',
            '資本剰余金', '利益剰余金', '自己株式', '評価換算差額等', '新株予約権',
            '販売費及び一般管理費',
            '現金及び預金', '売上債権', '棚卸資産', '有価証券', '投資その他の資産',
            '有形固定資産', '無形固定資産',
            '仕入債務', 'その他流動負債', 'その他流動資産',
            '販管費',
        }

        _SECTION_TO_CATEGORY = {
            '流動資産': ('資産', '流動資産', 'その他流動資産'),
            '現金及び預金': ('資産', '流動資産', '現金及び預金'),
            '現金・預金': ('資産', '流動資産', '現金及び預金'),
            '売上債権': ('資産', '流動資産', '売上債権'),
            '棚卸資産': ('資産', '流動資産', '棚卸資産'),
            '有価証券': ('資産', '流動資産', '有価証券'),
            'その他流動資産': ('資産', '流動資産', 'その他流動資産'),
            '固定資産': ('資産', '固定資産', 'その他流動資産'),
            '有形固定資産': ('資産', '固定資産', '有形固定資産'),
            '無形固定資産': ('資産', '固定資産', '無形固定資産'),
            '投資その他の資産': ('資産', '固定資産', '投資その他の資産'),
            '繰延資産': ('資産', '繰延資産', '繰延資産'),
            '流動負債': ('負債', '流動負債', 'その他流動負債'),
            '仕入債務': ('負債', '流動負債', '仕入債務'),
            'その他流動負債': ('負債', '流動負債', 'その他流動負債'),
            '固定負債': ('負債', '固定負債', '固定負債'),
            '純資産': ('純資産', '資本金', '資本金'),
            '資本金': ('純資産', '資本金', '資本金'),
            '資本剰余金': ('純資産', '資本剰余金', 'その他資本剰余金'),
            '利益剰余金': ('純資産', '利益剰余金', 'その他利益剰余金'),
            '自己株式': ('純資産', '自己株式', '自己株式'),
            '売上高': ('損益', '売上高', '売上高'),
            '売上原価': ('損益', '売上原価', '売上原価'),
            '販売費及び一般管理費': ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
            '販管費': ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
            '販売費': ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
            '一般管理費': ('損益', '販売費及び一般管理費', '販売費及び一般管理費'),
            '営業外収益': ('損益', '営業外収益', '営業外収益'),
            '営業外費用': ('損益', '営業外費用', '営業外費用'),
            '特別利益': ('損益', '特別利益', '特別利益'),
            '特別損失': ('損益', '特別損失', '特別損失'),
            '法人税等': ('損益', '法人税等', '法人税等'),
            '製造原価': ('損益', '売上原価', '売上原価'),
            '材料費': ('損益', '売上原価', '売上原価'),
            '労務費': ('損益', '売上原価', '売上原価'),
            '製造経費': ('損益', '売上原価', '売上原価'),
        }

        def _safe_load_items(items_json):
            if not items_json:
                return []
            try:
                items = json.loads(items_json)
            except (json.JSONDecodeError, TypeError, ValueError):
                return []
            return items if isinstance(items, list) else []

        def _sync_account_master_from_otb(items_json, account_model):
            items = _safe_load_items(items_json)
            if not items:
                return False

            existing_rows = {
                row.account_name: row
                for row in db.query(account_model).filter_by(tenant_id=tenant_id).all()
            }
            changed = False

            for order_idx, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                account_name = str(item.get('name') or item.get('account_name') or '').strip()
                if not account_name or account_name in _ACCOUNT_SECTION_NAMES:
                    continue

                section = str(item.get('section') or '').strip()
                cat = _SECTION_TO_CATEGORY.get(section)
                is_summary = _is_fixed_summary_account(account_name)
                row = existing_rows.get(account_name)

                if not row:
                    row = account_model(
                        tenant_id=tenant_id,
                        account_name=account_name,
                        display_order=order_idx,
                        is_auto_created=True,
                        major_category=cat[0] if cat else None,
                        mid_category=cat[1] if cat else None,
                        sub_category=cat[2] if cat else None,
                        category_status='confirmed' if cat else 'uncategorized',
                        target_statement=None,
                        target_field=None,
                        mapping_status='ignored' if is_summary else 'unmapped',
                    )
                    db.add(row)
                    db.flush()
                    existing_rows[account_name] = row
                    changed = True
                else:
                    if row.display_order != order_idx:
                        row.display_order = order_idx
                        changed = True

                if is_summary:
                    if row.target_statement is not None or row.target_field is not None or row.mapping_status != 'ignored' or row.ai_confidence is not None:
                        row.target_statement = None
                        row.target_field = None
                        row.mapping_status = 'ignored'
                        row.ai_confidence = None
                        changed = True

            return changed

        latest_otbs = (
            db.query(OriginalTrialBalance)
              .join(FiscalYear, OriginalTrialBalance.fiscal_year_id == FiscalYear.id)
              .join(Company, FiscalYear.company_id == Company.id)
              .filter(Company.tenant_id == tenant_id)
              .order_by(OriginalTrialBalance.updated_at.desc(), OriginalTrialBalance.id.desc())
              .all()
        )
        synced_stmt_types = {'pl': False, 'bs': False, 'mcr': False}
        sync_changed = False
        for otb in latest_otbs:
            if not synced_stmt_types['pl'] and getattr(otb, 'pl_items', None):
                sync_changed = _sync_account_master_from_otb(otb.pl_items, PlAccountItem) or sync_changed
                synced_stmt_types['pl'] = True
            if not synced_stmt_types['bs'] and getattr(otb, 'bs_items', None):
                sync_changed = _sync_account_master_from_otb(otb.bs_items, BsAccountItem) or sync_changed
                synced_stmt_types['bs'] = True
            if not synced_stmt_types['mcr'] and getattr(otb, 'mcr_items', None):
                sync_changed = _sync_account_master_from_otb(otb.mcr_items, McrAccountItem) or sync_changed
                synced_stmt_types['mcr'] = True
            if all(synced_stmt_types.values()):
                break

        if sync_changed:
            db.commit()

        def _build_order_map(items_json):
            items = _safe_load_items(items_json)
            if not items:
                return {}

            order_map = {}
            display_index = 0
            for item in items:
                if not isinstance(item, dict):
                    continue
                account_name = str(item.get('name') or item.get('account_name') or '').strip()
                if not account_name or account_name in _ACCOUNT_SECTION_NAMES:
                    continue
                if account_name not in order_map:
                    order_map[account_name] = display_index
                    display_index += 1
            return order_map

        statement_order_maps = {'pl': {}, 'bs': {}, 'mcr': {}}
        for otb in latest_otbs:
            if not statement_order_maps['pl'] and getattr(otb, 'pl_items', None):
                statement_order_maps['pl'] = _build_order_map(otb.pl_items)
            if not statement_order_maps['bs'] and getattr(otb, 'bs_items', None):
                statement_order_maps['bs'] = _build_order_map(otb.bs_items)
            if not statement_order_maps['mcr'] and getattr(otb, 'mcr_items', None):
                statement_order_maps['mcr'] = _build_order_map(otb.mcr_items)
            if all(order_map for order_map in statement_order_maps.values()):
                break

        field_order_maps = {
            'pl': {key: idx for idx, key in enumerate(_PL_FIELDS.keys())},
            'bs': {key: idx for idx, key in enumerate(_BS_FIELDS.keys())},
            'mcr': {key: idx for idx, key in enumerate(_MCR_FIELDS.keys())},
        }

        def _sort_items_for_display(items, stmt_type):
            order_map = statement_order_maps.get(stmt_type) or {}
            field_order_map = field_order_maps.get(stmt_type) or {}
            default_rank = 10 ** 9

            def _field_rank(row):
                target_field = row.get('target_field')
                return field_order_map.get(target_field, default_rank)

            def _anchor_rank(row):
                account_name = row.get('account_name')
                if account_name in order_map:
                    return order_map[account_name]
                if row.get('is_confirmed'):
                    return _field_rank(row)
                return default_rank

            return sorted(
                items,
                key=lambda row: (
                    _anchor_rank(row),
                    0 if row.get('is_summary') else 1,
                    _field_rank(row),
                    row.get('display_order') if row.get('display_order') is not None else default_rank,
                    row['id'],
                )
            )

        summary_sync = {'changed': False}

        def _clean_value(value):
            if value is None:
                return None
            value = str(value).strip()
            return value or None

        def _row_to_dict(ai, stmt_type):
            is_summary = _is_fixed_summary_account(ai.account_name)
            if is_summary and (ai.target_statement is not None or ai.target_field is not None or ai.mapping_status != 'ignored' or ai.ai_confidence is not None):
                ai.target_statement = None
                ai.target_field = None
                ai.mapping_status = 'ignored'
                ai.ai_confidence = None
                summary_sync['changed'] = True

            major_category = _clean_value(getattr(ai, 'major_category', None))
            mid_category = _clean_value(getattr(ai, 'mid_category', None))
            sub_category = _clean_value(getattr(ai, 'sub_category', None))
            target_field = None if is_summary else _clean_value(ai.target_field)
            target_statement = None if is_summary else _clean_value(ai.target_statement)

            if stmt_type == 'pl':
                major_category = '損益'
                valid_mid_categories = set(pl_category_tree.get('損益', {}).keys())
                if mid_category not in valid_mid_categories:
                    mid_category = None
                sub_category = None
                if target_field and target_field in _PL_FIELDS:
                    target_statement = 'PL'
                else:
                    target_field = None
                    target_statement = None
            elif stmt_type == 'bs':
                if major_category not in bs_category_tree:
                    major_category = None
                valid_mid_categories = set(bs_category_tree.get(major_category, {}).keys()) if major_category else set()
                if mid_category not in valid_mid_categories:
                    mid_category = None
                valid_sub_categories = set(bs_category_tree.get(major_category, {}).get(mid_category, [])) if major_category and mid_category else set()
                if sub_category not in valid_sub_categories:
                    sub_category = None
                if target_field and target_field in _BS_FIELDS:
                    target_statement = 'BS'
                else:
                    target_field = None
                    target_statement = None
            elif stmt_type == 'mcr':
                if major_category not in mcr_category_tree:
                    major_category = None
                valid_mid_categories = set(mcr_category_tree.get(major_category, {}).keys()) if major_category else set()
                if mid_category not in valid_mid_categories:
                    mid_category = None
                sub_category = None
                if target_field and target_field in _MCR_FIELDS:
                    target_statement = 'MCR'
                else:
                    target_field = None
                    target_statement = None

            is_confirmed = bool(not is_summary and major_category and mid_category and target_field)
            is_partial = bool(not is_summary and (major_category or mid_category or target_field))

            return {
                'id': ai.id,
                'account_name': ai.account_name,
                'display_order': getattr(ai, 'display_order', None),
                'is_auto_created': ai.is_auto_created,
                'is_summary': is_summary,
                'is_confirmed': is_confirmed,
                'is_partial': is_partial,
                'target_statement': target_statement,
                'target_field': target_field,
                'mapping_status': ai.mapping_status,
                'ai_confidence': ai.ai_confidence,
                'major_category': major_category,
                'mid_category': mid_category,
                'sub_category': sub_category,
                'category_status': getattr(ai, 'category_status', None),
            }

        pl_rows = db.query(PlAccountItem).filter_by(tenant_id=tenant_id).order_by(PlAccountItem.display_order, PlAccountItem.id).all()
        pl_items = _sort_items_for_display([_row_to_dict(ai, 'pl') for ai in pl_rows], 'pl')

        bs_rows = db.query(BsAccountItem).filter_by(tenant_id=tenant_id).order_by(BsAccountItem.display_order, BsAccountItem.id).all()
        bs_items = _sort_items_for_display([_row_to_dict(ai, 'bs') for ai in bs_rows], 'bs')

        mcr_rows = db.query(McrAccountItem).filter_by(tenant_id=tenant_id).order_by(McrAccountItem.display_order, McrAccountItem.id).all()
        mcr_items = _sort_items_for_display([_row_to_dict(ai, 'mcr') for ai in mcr_rows], 'mcr')

        if summary_sync['changed']:
            db.commit()

        return render_template('account_master.html',
                               pl_items=pl_items, bs_items=bs_items, mcr_items=mcr_items,
                               pl_fields=_PL_FIELDS, bs_fields=_BS_FIELDS, mcr_fields=_MCR_FIELDS,
                               all_fields=_ALL_FIELDS,
                               field_groups={'PL': _PL_FIELD_GROUPS, 'BS': _BS_FIELD_GROUPS, 'MCR': _MCR_FIELD_GROUPS},
                               pl_field_groups=_PL_FIELD_GROUPS,
                               bs_field_groups=_BS_FIELD_GROUPS,
                               mcr_field_groups=_MCR_FIELD_GROUPS,
                               category_tree=category_tree,
                               pl_category_tree=pl_category_tree,
                               bs_category_tree=bs_category_tree,
                               mcr_category_tree=mcr_category_tree)
    finally:
        db.close()


@bp.route('/account-master/<string:stmt_type>/<int:item_id>', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def account_master_update(stmt_type, item_id):
    """科目マスタ 1件更新（AJAX）"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        model_map = {'pl': PlAccountItem, 'bs': BsAccountItem, 'mcr': McrAccountItem}
        model = model_map.get(stmt_type)
        if not model:
            return jsonify({'success': False, 'error': '不正な帳票種別です'}), 400
        item = db.query(model).filter_by(id=item_id, tenant_id=tenant_id).first()
        if not item:
            return jsonify({'success': False, 'error': '科目が見つかりません'}), 404
        if _is_fixed_summary_account(item.account_name):
            return jsonify({'success': False, 'error': '集計行は編集できません'}), 400
        data = request.get_json() or {}

        if 'account_name' in data:
            account_name = (data.get('account_name') or '').strip()
            if not account_name:
                return jsonify({'success': False, 'error': '科目名は必須です'}), 400
            duplicate = db.query(model).filter(
                model.tenant_id == tenant_id,
                model.account_name == account_name,
                model.id != item_id
            ).first()
            if duplicate:
                return jsonify({'success': False, 'error': 'この科目名は既に登録されています'}), 409
            item.account_name = account_name

        raw_target_field = data.get('target_field') or None
        allowed_fields = None
        default_statement = None

        if stmt_type == 'pl':
            item.major_category = '損益'
            item.sub_category = None
            allowed_fields = _PL_FIELDS
            default_statement = 'PL'
        elif stmt_type == 'bs':
            allowed_fields = _BS_FIELDS
            default_statement = 'BS'
        elif stmt_type == 'mcr':
            item.sub_category = None
            allowed_fields = _MCR_FIELDS
            default_statement = 'MCR'

        if raw_target_field and allowed_fields is not None and raw_target_field not in allowed_fields:
            raw_target_field = None

        item.target_field = raw_target_field
        item.target_statement = default_statement if raw_target_field else None
        item.mapping_status = data.get('mapping_status', 'confirmed' if raw_target_field else 'pending')

        if 'major_category' in data and stmt_type != 'pl':
            item.major_category = data.get('major_category') or None
        if 'mid_category' in data:
            item.mid_category = data.get('mid_category') or None
        if 'sub_category' in data and stmt_type not in ('pl', 'mcr'):
            item.sub_category = data.get('sub_category') or None
        if 'category_status' in data:
            item.category_status = data.get('category_status') or None
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/account-master/<string:stmt_type>/<int:item_id>/delete', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def account_master_delete(stmt_type, item_id):
    """科目マスタ 1件削除（AJAX）"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        model_map = {'pl': PlAccountItem, 'bs': BsAccountItem, 'mcr': McrAccountItem}
        model = model_map.get(stmt_type)
        if not model:
            return jsonify({'success': False, 'error': '不正な帳票種別です'}), 400
        item = db.query(model).filter_by(id=item_id, tenant_id=tenant_id).first()
        if not item:
            return jsonify({'success': False, 'error': '科目が見つかりません'}), 404
        if _is_fixed_summary_account(item.account_name):
            return jsonify({'success': False, 'error': '集計行は削除できません'}), 400
        db.delete(item)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/account-master/<string:stmt_type>/add', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def account_master_add(stmt_type):
    """科目マスタ 1件追加（AJAX）"""
    tenant_id = session.get('tenant_id')
    db = SessionLocal()
    try:
        model_map = {'pl': PlAccountItem, 'bs': BsAccountItem, 'mcr': McrAccountItem}
        model = model_map.get(stmt_type)
        if not model:
            return jsonify({'success': False, 'error': '不正な帳票種別です'}), 400
        data = request.get_json() or {}
        account_name = (data.get('account_name') or '').strip()
        if not account_name:
            return jsonify({'success': False, 'error': '科目名は必須です'}), 400
        existing = db.query(model).filter_by(tenant_id=tenant_id, account_name=account_name).first()
        if existing:
            return jsonify({'success': False, 'error': 'この科目名は既に登録されています'}), 409
        raw_target_field = data.get('target_field') or None
        if stmt_type == 'pl':
            major_category = '損益'
            sub_category = None
            allowed_fields = _PL_FIELDS
            default_statement = 'PL'
        elif stmt_type == 'bs':
            major_category = data.get('major_category') or None
            sub_category = data.get('sub_category') or None
            allowed_fields = _BS_FIELDS
            default_statement = 'BS'
        else:
            major_category = data.get('major_category') or None
            sub_category = None
            allowed_fields = _MCR_FIELDS
            default_statement = 'MCR'

        if raw_target_field and raw_target_field not in allowed_fields:
            raw_target_field = None

        new_item = model(
            tenant_id=tenant_id,
            account_name=account_name,
            display_order=9999,
            is_auto_created=False,
            target_statement=default_statement if raw_target_field else None,
            target_field=raw_target_field,
            mapping_status='confirmed' if raw_target_field else 'pending',
            major_category=major_category,
            mid_category=data.get('mid_category') or None,
            sub_category=sub_category,
            category_status=data.get('category_status', 'uncategorized'),
        )
        db.add(new_item)
        db.commit()
        return jsonify({'success': True, 'id': new_item.id})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@bp.route('/account-master/ai-suggest', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def account_master_ai_suggest():
    """科目マスタ AI一括分類推定（AJAX）"""
    import json as _json
    import os as _os
    from openai import OpenAI

    data = request.get_json() or {}
    items = data.get('items', [])  # [{id, name, stmt_type}, ...]
    items = [it for it in items if not _is_fixed_summary_account(it.get('name'))]
    if not items:
        return jsonify({'success': True, 'suggestions': []})

    # OpenAI APIキーをDBから取得（他のエンドポイントと同様の方法）
    openai_api_key = None
    db = SessionLocal()
    try:
        current_user_id = session.get('user_id')
        if current_user_id:
            from ..models_login import TKanrisha as _TKanrisha
            current_user = db.query(_TKanrisha).filter(_TKanrisha.id == current_user_id).first()
            if current_user and current_user.openai_api_key and current_user.openai_api_key.strip():
                openai_api_key = current_user.openai_api_key.strip()
        if not openai_api_key:
            from ..models_login import TKanrisha as _TKanrisha
            sys_admin = db.query(_TKanrisha).filter(
                _TKanrisha.openai_api_key != None,
                _TKanrisha.openai_api_key != ''
            ).first()
            if sys_admin and sys_admin.openai_api_key:
                openai_api_key = sys_admin.openai_api_key.strip()
    except Exception as e:
        return jsonify({'success': False, 'error': f'DBエラー: {str(e)}'}), 500
    finally:
        db.close()

    if not openai_api_key:
        return jsonify({'success': False, 'error': 'OpenAI APIキーが設定されていません。システム管理者にAPIキーの設定を依頼してください。'}), 400

    cat_json_path = _os.path.join(_os.path.dirname(__file__), 'account_item_categories.json')
    try:
        with open(cat_json_path, 'r', encoding='utf-8') as f:
            category_tree = _json.load(f)
    except Exception as e:
        return jsonify({'success': False, 'error': f'カテゴリファイルの読み込みに失敗: {str(e)}'}), 500

    all_fields_str = _json.dumps({
        'PL': _PL_FIELDS,
        'BS': _BS_FIELDS,
        'MCR': _MCR_FIELDS,
    }, ensure_ascii=False)

    category_tree_str = _json.dumps(category_tree, ensure_ascii=False)
    items_str = _json.dumps(
        [{'id': it['id'], 'name': it['name'], 'stmt_type': it['stmt_type']} for it in items],
        ensure_ascii=False
    )

    # 分類ツリーの小分類キーを明示的にリスト化してプロンプトに含める
    sub_category_map = {}
    for major, mids in category_tree.items():
        for mid, subs in mids.items():
            if isinstance(subs, dict):
                sub_category_map[f"{major}>{mid}"] = list(subs.keys())
            elif isinstance(subs, list):
                sub_category_map[f"{major}>{mid}"] = subs
    sub_category_map_str = _json.dumps(sub_category_map, ensure_ascii=False)

    prompt = f"""あなたは日本の財務諸表の勘定科目分類の専門家です。
以下の勘定科目リストに対して、大分類・中分類・小分類・組換え先帳票・組換え先科目を推定してください。

## 分類ツリー（大分類 > 中分類 > 小分類）
{category_tree_str}

## 小分類の選択肢（"大分類>中分類": [使用可能な小分類リスト]）
{sub_category_map_str}

## 組換え先フィールド一覧
{all_fields_str}

## 勘定科目リスト
{items_str}

## 出力形式
以下のJSON配列のみを返してください（説明不要）：
[
  {{
    "id": <科目ID>,
    "major_category": "<大分類（分類ツリーの最上位キー）>",
    "mid_category": "<中分類（大分類の下のキー）>",
    "sub_category": "<小分類（上記の小分類選択肢リストから選ぶ。該当なければ空文字）>",
    "target_statement": "<組換え先帳票: PL/BS/空文字>",
    "target_field": "<組換え先科目のキー（組換え先フィールド一覧のキー）、なければ空文字>"
  }}
]

## ルール
- 合計行（〜合計、〜計、〜小計）は target_statement と target_field を空文字にする
- stmt_type が 'pl' の科目は major_category を必ず '損益' にする
- stmt_type が 'pl' の科目は target_statement を 'PL' または空文字にする
- stmt_type が 'pl' の科目は target_field に必ず PLフィールドのキーのみ使用する（BS・ MCRフィールドのキーは絶対使用しない）
- stmt_type が 'bs' の科目は target_statement を 'BS' または空文字にする
- stmt_type が 'bs' の科目は target_field に必ず BSフィールドのキーのみ使用する
- stmt_type が 'mcr' の科目は target_statement を 'MCR' または空文字にする
- stmt_type が 'mcr' の科目は target_field に必ず MCRフィールドのキーのみ使用する
- sub_category は必ず上記の小分類選択肢リストに存在する値を使用すること。存在しない値は絶対に使用しない
- 分類ツリーに存在しないカテゴリは使用しない
- 組換え先フィールドに存在しないキーは使用しない
"""

    try:
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
    except Exception as e:
        return jsonify({'success': False, 'error': f'OpenAI API呼び出しエラー: {str(e)}'}), 500

    raw = response.choices[0].message.content.strip()
    if '```' in raw:
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]
    try:
        suggestions = _json.loads(raw)
    except Exception as e:
        return jsonify({'success': False, 'error': f'AI応答のパースに失敗: {str(e)}', 'raw': raw}), 500

    # PLの大分類を強制的に「損益」に上書き、MCRキーが混入した場合はnullに変換
    pl_keys = set(_PL_FIELDS.keys())
    bs_keys = set(_BS_FIELDS.keys())
    mcr_keys = set(_MCR_FIELDS.keys())
    stmt_type_map = {it['id']: it['stmt_type'] for it in items}
    for s in suggestions:
        stype = stmt_type_map.get(s.get('id'))
        if stype == 'pl':
            s['major_category'] = '損益'
            s['sub_category'] = ''
            if s.get('target_field') and s['target_field'] in pl_keys:
                s['target_statement'] = 'PL'
            else:
                s['target_field'] = ''
                s['target_statement'] = ''
        elif stype == 'bs':
            if s.get('target_field') and s['target_field'] in bs_keys:
                s['target_statement'] = 'BS'
            else:
                s['target_field'] = ''
                s['target_statement'] = ''
        elif stype == 'mcr':
            s['sub_category'] = ''
            if s.get('target_field') and s['target_field'] in mcr_keys:
                s['target_statement'] = 'MCR'
            else:
                s['target_field'] = ''
                s['target_statement'] = ''
    return jsonify({'success': True, 'suggestions': suggestions})


@bp.route('/account-master/bulk-save', methods=['POST'])
@require_roles(ROLES["TENANT_ADMIN"], ROLES["SYSTEM_ADMIN"])
def account_master_bulk_save():
    """科目マスタ 一括保存（AJAX）"""
    tenant_id = session.get('tenant_id')
    data = request.get_json() or {}
    items = data.get('items', [])  # [{id, stmt_type, account_name, major_category, mid_category, sub_category, target_statement, target_field}, ...]
    if not items:
        return jsonify({'success': False, 'error': '保存する科目がありません'}), 400

    db = SessionLocal()
    try:
        model_map = {'pl': PlAccountItem, 'bs': BsAccountItem, 'mcr': McrAccountItem}
        saved_count = 0
        errors = []
        for it in items:
            stmt_type = it.get('stmt_type', '').lower()
            item_id = it.get('id')
            model = model_map.get(stmt_type)
            if not model or not item_id:
                errors.append(f'不正なデータ: {it}')
                continue
            item = db.query(model).filter_by(id=item_id, tenant_id=tenant_id).first()
            if not item:
                errors.append(f'科目ID {item_id} が見つかりません')
                continue
            if _is_fixed_summary_account(item.account_name):
                continue

            account_name = (it.get('account_name') or '').strip()
            if not account_name:
                errors.append(f'科目ID {item_id}: 科目名は必須です')
                continue
            duplicate = db.query(model).filter(
                model.tenant_id == tenant_id,
                model.account_name == account_name,
                model.id != item_id
            ).first()
            if duplicate:
                errors.append(f'科目ID {item_id}: この科目名は既に登録されています')
                continue
            item.account_name = account_name

            if stmt_type == 'pl':
                item.major_category = '損益'
                item.sub_category = None
                allowed_fields = _PL_FIELDS
                default_statement = 'PL'
            elif stmt_type == 'bs':
                item.major_category = it.get('major_category') or None
                item.sub_category = it.get('sub_category') or None
                allowed_fields = _BS_FIELDS
                default_statement = 'BS'
            else:
                item.major_category = it.get('major_category') or None
                item.sub_category = None
                allowed_fields = _MCR_FIELDS
                default_statement = 'MCR'
            item.mid_category = it.get('mid_category') or None
            # 各帳票種別に正しいフィールドキーのみ許可するバリデーション
            raw_tf = it.get('target_field') or None
            if raw_tf and raw_tf not in allowed_fields:
                raw_tf = None
            item.target_statement = default_statement if raw_tf else None
            item.target_field = raw_tf
            # 組換え先科目が設定されている場合のみ確定済にする
            if item.target_field:
                item.mapping_status = 'confirmed'
            else:
                item.mapping_status = 'pending'
            saved_count += 1
        db.commit()
        return jsonify({'success': True, 'saved_count': saved_count, 'errors': errors})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()
