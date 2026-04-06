"""
データベースモデル定義
経営意思決定支援システムのデータベーススキーマ
Node.js版（management-decision-making-app）の全テーブルをPythonに移植
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum, JSON, Numeric
from sqlalchemy.orm import relationship
import enum

# login-system-appのBaseを使用
from app.db import Base


# ==================== 企業・会計年度 ====================

class Company(Base):
    """企業マスタ"""
    __tablename__ = 'companies'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, index=True)  # テナントID
    name = Column(String(255), nullable=False)
    industry = Column(String(100))  # 業種
    capital = Column(Integer)  # 資本金
    employee_count = Column(Integer)  # 従業員数
    established_date = Column(Date)  # 設立日
    address = Column(Text)  # 住所
    phone = Column(String(20))  # 電話番号
    email = Column(String(320))  # メールアドレス
    website = Column(String(500))  # ウェブサイト
    notes = Column(Text)  # 備考
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_years = relationship("FiscalYear", back_populates="company", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="company", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="company", cascade="all, delete-orphan")
    differential_analyses = relationship("DifferentialAnalysis", back_populates="company", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="company", cascade="all, delete-orphan")
    account_mappings = relationship("AccountMapping", back_populates="company", cascade="all, delete-orphan")


class FiscalYear(Base):
    """会計年度テーブル"""
    __tablename__ = 'fiscal_years'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    year_name = Column(String(100), nullable=False)  # 年度名（例: 2024年度）
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    months = Column(Integer, default=12)  # 月数
    notes = Column(Text)  # 備考
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company", back_populates="fiscal_years")
    profit_loss_statement = relationship("ProfitLossStatement", back_populates="fiscal_year", uselist=False, cascade="all, delete-orphan")
    balance_sheet = relationship("BalanceSheet", back_populates="fiscal_year", uselist=False, cascade="all, delete-orphan")
    restructured_pl = relationship("RestructuredPL", back_populates="fiscal_year", uselist=False, cascade="all, delete-orphan")
    restructured_bs = relationship("RestructuredBS", back_populates="fiscal_year", uselist=False, cascade="all, delete-orphan")
    manufacturing_cost_report = relationship("ManufacturingCostReport", back_populates="fiscal_year", uselist=False, cascade="all, delete-orphan")
    labor_cost = relationship("LaborCost", back_populates="fiscal_year", uselist=False, cascade="all, delete-orphan")
    financial_indicators = relationship("FinancialIndicator", back_populates="fiscal_year", cascade="all, delete-orphan")
    business_segments = relationship("BusinessSegment", back_populates="fiscal_year", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="fiscal_year", cascade="all, delete-orphan")
    annual_budgets = relationship("AnnualBudget", back_populates="fiscal_year", cascade="all, delete-orphan")
    cash_flow_plans = relationship("CashFlowPlan", back_populates="fiscal_year", cascade="all, delete-orphan")
    labor_plans = relationship("LaborPlan", back_populates="fiscal_year", cascade="all, delete-orphan")
    capital_investment_plans = relationship("CapitalInvestmentPlan", back_populates="fiscal_year", cascade="all, delete-orphan")


# ==================== 財務諸表（簡易版） ====================

class ProfitLossStatement(Base):
    """損益計算書（簡易版）"""
    __tablename__ = 'profit_loss_statements'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    
    # 売上関連
    sales = Column(Integer, default=0, nullable=False)
    cost_of_sales = Column(Integer, default=0, nullable=False)
    gross_profit = Column(Integer, default=0, nullable=False)
    
    # 営業関連
    operating_expenses = Column(Integer, default=0, nullable=False)
    operating_income = Column(Integer, default=0, nullable=False)
    
    # 営業外
    non_operating_income = Column(Integer, default=0, nullable=False)
    non_operating_expenses = Column(Integer, default=0, nullable=False)
    ordinary_income = Column(Integer, default=0, nullable=False)
    
    # 特別損益
    extraordinary_income = Column(Integer, default=0, nullable=False)
    extraordinary_loss = Column(Integer, default=0, nullable=False)
    
    # 税引前・税引後
    income_before_tax = Column(Integer, default=0, nullable=False)
    income_tax = Column(Integer, default=0, nullable=False)
    net_income = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="profit_loss_statement")


class BalanceSheet(Base):
    """貸借対照表（簡易版）"""
    __tablename__ = 'balance_sheets'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    
    # 資産
    current_assets = Column(Integer, default=0, nullable=False)
    fixed_assets = Column(Integer, default=0, nullable=False)
    total_assets = Column(Integer, default=0, nullable=False)
    
    # 担保力計算用の追加項目
    land_market_value = Column(Integer, default=0, nullable=False)  # 土地（時価）
    securities_market_value = Column(Integer, default=0, nullable=False)  # 有価証券（時価）
    
    # 負債
    current_liabilities = Column(Integer, default=0, nullable=False)
    fixed_liabilities = Column(Integer, default=0, nullable=False)
    total_liabilities = Column(Integer, default=0, nullable=False)
    
    # 純資産
    capital = Column(Integer, default=0, nullable=False)
    retained_earnings = Column(Integer, default=0, nullable=False)
    total_equity = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="balance_sheet")


# ==================== 財務諸表（組換え版） ====================

class RestructuredPL(Base):
    """組換え損益計算書（詳細版）"""
    __tablename__ = 'restructured_pl'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    
    # 1. 売上高
    sales = Column(Integer, default=0, nullable=False)
    # 2. 売上原価
    cost_of_sales = Column(Integer, default=0, nullable=False)
    # 売上原価内訳
    beginning_inventory = Column(Integer, default=0, nullable=False)      # 期首棚卸高
    manufacturing_cost = Column(Integer, default=0, nullable=False)        # 当期製造（工事）原価
    ending_inventory = Column(Integer, default=0, nullable=False)          # 期末棚卸高
    # 売上総利益
    gross_profit = Column(Integer, default=0, nullable=False)
    # 外部経費調整（労務費＋減価償却費＋修繕費）
    external_cost_adjustment = Column(Integer, default=0, nullable=False)
    # 粗付加価値（売上総利益＋外部経費調整）
    gross_added_value = Column(Integer, default=0, nullable=False)
    # 3. 販売費及び一般管理費
    selling_general_admin_expenses = Column(Integer, default=0, nullable=False)
    # 販管費内訳
    labor_cost = Column(Integer, default=0, nullable=False)                # 人件費
    executive_compensation = Column(Integer, default=0, nullable=False)    # 役員報酬
    capital_regeneration_cost = Column(Integer, default=0, nullable=False) # 資本再生費（減価償却費＋修繕費）
    research_development_expenses = Column(Integer, default=0, nullable=False)  # 研究開発費
    general_expenses = Column(Integer, default=0, nullable=False)          # 一般経費
    general_expenses_fixed = Column(Integer, default=0, nullable=False)    # 一般経費（固定費）
    general_expenses_variable = Column(Integer, default=0, nullable=False) # 一般経費（変動費）
    # 営業利益
    operating_income = Column(Integer, default=0, nullable=False)
    # 4. 営業外損益
    financial_profit_loss = Column(Integer, default=0, nullable=False)     # 金融損益（受取利息－支払利息）
    other_non_operating = Column(Integer, default=0, nullable=False)       # その他の損益
    # 経常利益
    ordinary_income = Column(Integer, default=0, nullable=False)
    # 5. 特別損益
    extraordinary_profit_loss = Column(Integer, default=0, nullable=False) # 特別損益合計
    # 税引前当期純利益
    income_before_tax = Column(Integer, default=0, nullable=False)
    # 法人税等
    income_taxes = Column(Integer, default=0, nullable=False)
    # 当期純利益
    net_income = Column(Integer, default=0, nullable=False)
    # 6. 利益処分
    dividend = Column(Integer, default=0, nullable=False)                  # 配当金
    retained_profit = Column(Integer, default=0, nullable=False)           # 内部留保
    legal_reserve = Column(Integer, default=0, nullable=False)             # 利益準備金積立額
    voluntary_reserve = Column(Integer, default=0, nullable=False)         # その他剰余金積立額
    retained_earnings_increase = Column(Integer, default=0, nullable=False) # 繰越利益剰余金増加
    
    # 旧フィールド（後方互換性）
    non_operating_income = Column(Integer, default=0, nullable=False)
    non_operating_expenses = Column(Integer, default=0, nullable=False)
    extraordinary_income = Column(Integer, default=0, nullable=False)
    extraordinary_loss = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="restructured_pl")


class RestructuredBS(Base):
    """組換え貸借対照表（詳細版）"""
    __tablename__ = 'restructured_bs'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    
    # ===== 資産の部 =====
    # 1. 当座資産
    cash_on_hand = Column(Integer, default=0, nullable=False)              # 手許現預金
    investment_deposits = Column(Integer, default=0, nullable=False)       # 運用預金
    marketable_securities = Column(Integer, default=0, nullable=False)     # 有価証券
    # 2. 売掛債権
    trade_receivables = Column(Integer, default=0, nullable=False)         # 売掛債権（売掛金＋受取手形）
    # 3. 棚卸資産
    inventory_assets = Column(Integer, default=0, nullable=False)          # 棚卸資産
    # 流動資産合計
    current_assets = Column(Integer, default=0, nullable=False)
    # 固定資産
    tangible_fixed_assets = Column(Integer, default=0, nullable=False)     # 有形固定資産
    intangible_fixed_assets = Column(Integer, default=0, nullable=False)   # 無形固定資産
    investments_and_other = Column(Integer, default=0, nullable=False)     # 投資その他資産
    deferred_assets = Column(Integer, default=0, nullable=False)           # 繰延資産
    fixed_assets = Column(Integer, default=0, nullable=False)
    # 資産合計
    total_assets = Column(Integer, default=0, nullable=False)
    
    # ===== 負債の部 =====
    # 4. 買掛債務
    trade_payables = Column(Integer, default=0, nullable=False)            # 買掛債務
    # 5. 短期借入金（1年以内返済の長期借入金を含む）
    short_term_borrowings = Column(Integer, default=0, nullable=False)     # 短期借入金
    current_portion_long_term = Column(Integer, default=0, nullable=False) # 1年以内返済の長期借入金
    discounted_notes = Column(Integer, default=0, nullable=False)          # 割引手形
    other_current_liabilities = Column(Integer, default=0, nullable=False) # その他流動負債
    # 流動負債合計
    current_liabilities = Column(Integer, default=0, nullable=False)
    # 6. 長期借入金
    long_term_borrowings = Column(Integer, default=0, nullable=False)      # 長期借入金
    executive_borrowings = Column(Integer, default=0, nullable=False)      # 役員等借入金
    retirement_benefit_liability = Column(Integer, default=0, nullable=False)  # 退職給付引当金
    other_fixed_liabilities = Column(Integer, default=0, nullable=False)   # その他固定負債
    # 固定負債合計
    fixed_liabilities = Column(Integer, default=0, nullable=False)
    # 負債合計
    total_liabilities = Column(Integer, default=0, nullable=False)
    
    # ===== 純資産の部 =====
    capital = Column(Integer, default=0, nullable=False)                   # 資本金
    capital_surplus = Column(Integer, default=0, nullable=False)           # 資本剰余金
    retained_earnings = Column(Integer, default=0, nullable=False)         # 利益剰余金
    legal_reserve_bs = Column(Integer, default=0, nullable=False)          # 利益準備金
    voluntary_reserve_bs = Column(Integer, default=0, nullable=False)      # 任意積立金
    retained_earnings_carried = Column(Integer, default=0, nullable=False) # 繰越利益剰余金
    treasury_stock = Column(Integer, default=0, nullable=False)            # 自己株式
    # 純資産合計
    net_assets = Column(Integer, default=0, nullable=False)
    # 負債純資産合計
    total_liabilities_and_net_assets = Column(Integer, default=0, nullable=False)
    
    # 脈診注記
    discounted_notes_note = Column(Integer, default=0, nullable=False)     # 割引手形高（脈診）
    endorsed_notes_note = Column(Integer, default=0, nullable=False)       # 裏書手形高（脈診）
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="restructured_bs")


class ManufacturingCostReport(Base):
    """製造原価報告書（PDF読み取り版）"""
    __tablename__ = 'manufacturing_cost_reports'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    
    # ===== 材料費 =====
    beginning_raw_material = Column(Integer, default=0, nullable=False)       # 期首原材料棚卸高
    raw_material_purchase = Column(Integer, default=0, nullable=False)        # 当期原材料仕入高
    ending_raw_material = Column(Integer, default=0, nullable=False)          # 期末原材料棚卸高
    material_cost = Column(Integer, default=0, nullable=False)                # 材料費計
    
    # ===== 労務費 =====
    labor_cost_manufacturing = Column(Integer, default=0, nullable=False)     # 労務費計
    
    # ===== 製造経費 =====
    outsourcing_cost = Column(Integer, default=0, nullable=False)             # 外注加工費
    freight_manufacturing = Column(Integer, default=0, nullable=False)        # 荷造運賃（製造）
    meeting_cost_manufacturing = Column(Integer, default=0, nullable=False)   # 会議費（製造）
    travel_cost_manufacturing = Column(Integer, default=0, nullable=False)    # 旅費交通費（製造）
    communication_cost_manufacturing = Column(Integer, default=0, nullable=False)  # 通信費（製造）
    supplies_manufacturing = Column(Integer, default=0, nullable=False)       # 消耗品費（製造）
    vehicle_cost_manufacturing = Column(Integer, default=0, nullable=False)   # 車両費（製造）
    rent_manufacturing = Column(Integer, default=0, nullable=False)           # 賃借料（製造）
    insurance_manufacturing = Column(Integer, default=0, nullable=False)      # 保険料（製造）
    depreciation_manufacturing = Column(Integer, default=0, nullable=False)   # 減価償却費（製造）
    repair_cost_manufacturing = Column(Integer, default=0, nullable=False)    # 修繕費（製造）
    other_manufacturing_cost = Column(Integer, default=0, nullable=False)     # その他製造経費
    manufacturing_expenses_total = Column(Integer, default=0, nullable=False) # 製造経費計
    
    # ===== 合計 =====
    total_manufacturing_cost_current = Column(Integer, default=0, nullable=False)  # 総製造費用
    beginning_wip = Column(Integer, default=0, nullable=False)               # 期首仕掛品棚卸高
    ending_wip = Column(Integer, default=0, nullable=False)                  # 期末仕掛品棚卸高
    total_manufacturing_cost = Column(Integer, default=0, nullable=False)    # 製造原価合計
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="manufacturing_cost_report")


# ==================== 人件費・労務管理 ====================

class LaborCost(Base):
    """人件費データ"""
    __tablename__ = 'labor_costs'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    employee_count = Column(Integer, default=0, nullable=False)
    total_salary = Column(Integer, default=0, nullable=False)
    bonus = Column(Integer, default=0, nullable=False)
    retirement_allowance = Column(Integer, default=0, nullable=False)
    statutory_welfare = Column(Integer, default=0, nullable=False)
    welfare_expenses = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="labor_cost")


class LaborPlan(Base):
    """労務費管理計画（月次）"""
    __tablename__ = 'labor_plans'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    
    # 計画値
    planned_headcount = Column(Integer, default=0, nullable=False)
    planned_average_salary = Column(Integer, default=0, nullable=False)
    planned_total_labor_cost = Column(Integer, default=0, nullable=False)
    planned_bonuses = Column(Integer, default=0, nullable=False)
    planned_social_insurance = Column(Integer, default=0, nullable=False)
    
    # 実績値
    actual_headcount = Column(Integer, default=0, nullable=False)
    actual_average_salary = Column(Integer, default=0, nullable=False)
    actual_total_labor_cost = Column(Integer, default=0, nullable=False)
    actual_bonuses = Column(Integer, default=0, nullable=False)
    actual_social_insurance = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="labor_plans")


# ==================== 経営分析 ====================

class IndicatorType(enum.Enum):
    """財務指標タイプ"""
    GROWTH = "growth"  # 成長力
    PROFITABILITY = "profitability"  # 収益力
    LIQUIDITY = "liquidity"  # 資金力
    PRODUCTIVITY = "productivity"  # 生産力


class FinancialIndicator(Base):
    """財務指標データ"""
    __tablename__ = 'financial_indicators'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    indicator_type = Column(SQLEnum(IndicatorType), nullable=False)
    indicator_name = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    unit = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="financial_indicators")


class SegmentType(enum.Enum):
    """セグメントタイプ"""
    DEPARTMENT = "department"  # 部門
    PRODUCT = "product"  # 製品
    BUSINESS = "business"  # 事業
    REGION = "region"  # 地域


class BusinessSegment(Base):
    """事業セグメント（貢献度分析用）"""
    __tablename__ = 'business_segments'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    segment_name = Column(String(255), nullable=False)
    segment_type = Column(SQLEnum(SegmentType), nullable=False)
    sales = Column(Integer, default=0, nullable=False)
    operating_income = Column(Integer, default=0, nullable=False)
    assets = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="business_segments")


# ==================== 差額原価収益分析 ====================

class DifferentialAnalysis(Base):
    """差額原価収益分析マスタ"""
    __tablename__ = 'differential_analyses'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    analysis_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company", back_populates="differential_analyses")
    scenarios = relationship("DifferentialScenario", back_populates="analysis", cascade="all, delete-orphan")


class DifferentialScenario(Base):
    """差額原価収益分析シナリオ"""
    __tablename__ = 'differential_scenarios'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('differential_analyses.id'), nullable=False)
    scenario_name = Column(String(255), nullable=False)
    sales = Column(Integer, default=0, nullable=False)
    variable_costs = Column(Integer, default=0, nullable=False)
    fixed_costs = Column(Integer, default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    analysis = relationship("DifferentialAnalysis", back_populates="scenarios")


# ==================== 予算・計画管理 ====================

class Budget(Base):
    """予算管理（月次）"""
    __tablename__ = 'budgets'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    
    # 予算
    budget_sales = Column(Integer, default=0, nullable=False)
    budget_cogs = Column(Integer, default=0, nullable=False)
    budget_sga = Column(Integer, default=0, nullable=False)
    
    # 実績
    actual_sales = Column(Integer, default=0, nullable=False)
    actual_cogs = Column(Integer, default=0, nullable=False)
    actual_sga = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="budgets")


class CashFlowPlan(Base):
    """資金繰り計画（月次）"""
    __tablename__ = 'cash_flow_plans'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    
    # 期首残高
    opening_balance = Column(Integer, default=0, nullable=False)
    
    # 収入計画
    planned_sales_receipts = Column(Integer, default=0, nullable=False)
    planned_other_receipts = Column(Integer, default=0, nullable=False)
    planned_total_receipts = Column(Integer, default=0, nullable=False)
    
    # 支出計画
    planned_purchase_payments = Column(Integer, default=0, nullable=False)
    planned_labor_costs = Column(Integer, default=0, nullable=False)
    planned_expenses = Column(Integer, default=0, nullable=False)
    planned_loan_repayments = Column(Integer, default=0, nullable=False)
    planned_other_payments = Column(Integer, default=0, nullable=False)
    planned_total_payments = Column(Integer, default=0, nullable=False)
    
    # 期末残高（計画）
    planned_closing_balance = Column(Integer, default=0, nullable=False)
    
    # 実績収入
    actual_sales_receipts = Column(Integer, default=0, nullable=False)
    actual_other_receipts = Column(Integer, default=0, nullable=False)
    actual_total_receipts = Column(Integer, default=0, nullable=False)
    
    # 実績支出
    actual_purchase_payments = Column(Integer, default=0, nullable=False)
    actual_labor_costs = Column(Integer, default=0, nullable=False)
    actual_expenses = Column(Integer, default=0, nullable=False)
    actual_loan_repayments = Column(Integer, default=0, nullable=False)
    actual_other_payments = Column(Integer, default=0, nullable=False)
    actual_total_payments = Column(Integer, default=0, nullable=False)
    
    # 期末残高（実績）
    actual_closing_balance = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="cash_flow_plans")


class InvestmentStatus(enum.Enum):
    """設備投資ステータス"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CapitalInvestmentPlan(Base):
    """設備投資計画"""
    __tablename__ = 'capital_investment_plans'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    investment_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    
    # 計画値
    planned_amount = Column(Integer, default=0, nullable=False)
    planned_start_date = Column(DateTime)
    planned_completion_date = Column(DateTime)
    expected_roi = Column(Numeric(5, 2), default=0.00)
    expected_payback_period = Column(Integer, default=0)
    
    # 実績値
    actual_amount = Column(Integer, default=0, nullable=False)
    actual_start_date = Column(DateTime)
    actual_completion_date = Column(DateTime)
    actual_roi = Column(Numeric(5, 2), default=0.00)
    
    # ステータス
    status = Column(SQLEnum(InvestmentStatus), default=InvestmentStatus.PLANNED, nullable=False)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="capital_investment_plans")


# ==================== 借入金管理 ====================

class Loan(Base):
    """借入金マスタ"""
    __tablename__ = 'loans'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    loan_name = Column(String(255), nullable=False)
    lender = Column(String(255), nullable=False)
    loan_amount = Column(Integer, nullable=False)
    interest_rate = Column(Integer, nullable=False)  # 年利（%）を100倍した整数（例: 2.5% → 250）
    loan_date = Column(DateTime, nullable=False)
    repayment_start_date = Column(DateTime, nullable=False)
    repayment_end_date = Column(DateTime, nullable=False)
    monthly_repayment = Column(Integer, nullable=False)
    repayment_method = Column(String(50), nullable=False)  # 元利均等、元金均等など
    status = Column(String(50), default="active", nullable=False)  # active, completed
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company", back_populates="loans")
    repayments = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")


class LoanRepayment(Base):
    """返済実績"""
    __tablename__ = 'loan_repayments'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey('loans.id'), nullable=False)
    repayment_date = Column(DateTime, nullable=False)
    principal_amount = Column(Integer, nullable=False)
    interest_amount = Column(Integer, nullable=False)
    total_amount = Column(Integer, nullable=False)
    remaining_balance = Column(Integer, nullable=False)
    status = Column(String(50), default="scheduled", nullable=False)  # scheduled, paid
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    loan = relationship("Loan", back_populates="repayments")


# ==================== シミュレーション ====================

class Simulation(Base):
    """シミュレーション"""
    __tablename__ = 'simulations'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    simulation_name = Column(String(255), nullable=False)
    base_fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    parameters = Column(Text)  # JSON形式でパラメータを保存
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company", back_populates="simulations")
    results = relationship("SimulationResult", back_populates="simulation", cascade="all, delete-orphan")


class SimulationResult(Base):
    """シミュレーション結果"""
    __tablename__ = 'simulation_results'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'), nullable=False)
    year_offset = Column(Integer, nullable=False)  # 0, 1, 2（初年度、2年度、3年度）
    pl_data = Column(Text, nullable=False)  # JSON形式でP/Lデータを保存
    bs_data = Column(Text, nullable=False)  # JSON形式でB/Sデータを保存
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    simulation = relationship("Simulation", back_populates="results")


# ==================== その他 ====================

class NotificationType(enum.Enum):
    """通知タイプ"""
    CASH_SHORTAGE = "cash_shortage"
    FINANCIAL_INDICATOR_CHANGE = "financial_indicator_change"
    BUDGET_ALERT = "budget_alert"
    LOAN_ALERT = "loan_alert"


class NotificationSeverity(enum.Enum):
    """通知重要度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Notification(Base):
    """通知"""
    __tablename__ = 'notifications'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(SQLEnum(NotificationSeverity), default=NotificationSeverity.INFO, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    related_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company", back_populates="notifications")


class StatementType(enum.Enum):
    """財務諸表タイプ"""
    PL = "PL"
    BS = "BS"


class AccountMapping(Base):
    """勘定科目マッピング（財務諸表組換え用）"""
    __tablename__ = 'account_mappings'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    source_account = Column(String(255), nullable=False)  # 元の勘定科目名
    target_category = Column(String(100), nullable=False)  # 標準カテゴリ
    statement_type = Column(SQLEnum(StatementType), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company", back_populates="account_mappings")


# ==================== 年次予算管理 ====================

class AnnualBudget(Base):
    """年次予算テーブル"""
    __tablename__ = 'annual_budgets'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    
    # 損益計算書予算
    budget_sales = Column(Numeric(15, 2))  # 予算売上高
    budget_cost_of_sales = Column(Numeric(15, 2))  # 予算売上原価
    budget_gross_profit = Column(Numeric(15, 2))  # 予算売上総利益
    budget_operating_expenses = Column(Numeric(15, 2))  # 予算販管費
    budget_operating_income = Column(Numeric(15, 2))  # 予算営業利益
    budget_non_operating_income = Column(Numeric(15, 2))  # 予算営業外収益
    budget_non_operating_expenses = Column(Numeric(15, 2))  # 予算営業外費用
    budget_ordinary_income = Column(Numeric(15, 2))  # 予算経常利益
    budget_extraordinary_income = Column(Numeric(15, 2))  # 予算特別利益
    budget_extraordinary_loss = Column(Numeric(15, 2))  # 予算特別損失
    budget_income_before_tax = Column(Numeric(15, 2))  # 予算税引前当期純利益
    budget_income_tax = Column(Numeric(15, 2))  # 予算法人税等
    budget_net_income = Column(Numeric(15, 2))  # 予算当期純利益
    
    # 貸借対照表予算
    budget_current_assets = Column(Numeric(15, 2))  # 予算流動資産
    budget_fixed_assets = Column(Numeric(15, 2))  # 予算固定資産
    budget_total_assets = Column(Numeric(15, 2))  # 予算総資産
    budget_current_liabilities = Column(Numeric(15, 2))  # 予算流動負債
    budget_fixed_liabilities = Column(Numeric(15, 2))  # 予算固定負債
    budget_total_liabilities = Column(Numeric(15, 2))  # 予算総負債
    budget_total_equity = Column(Numeric(15, 2))  # 予算純資産
    
    # メタデータ
    notes = Column(Text)  # 備考
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    fiscal_year = relationship("FiscalYear", back_populates="annual_budgets")


# ==================== 複数年度計画統合管理 ====================

class MultiYearPlan(Base):
    """複数年度計画統合テーブル（3期分の個別計画を統合管理）"""
    __tablename__ = 'multi_year_plans'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    base_fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    
    # 3年分の計画データをJSONで格納
    years = Column(JSON, nullable=False)
    # 構造例:
    # {
    #   "year1": {
    #     "laborPlan": {...},
    #     "capexPlan": {...},
    #     "workingCapitalPlan": {...},
    #     "financingPlan": {...},
    #     "repaymentPlan": {...}
    #   },
    #   "year2": {...},
    #   "year3": {...}
    # }
    
    # メタデータ
    notes = Column(Text)  # 備考
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company", backref="multi_year_plans")
    base_fiscal_year = relationship("FiscalYear", foreign_keys=[base_fiscal_year_id])


# ==================== 運転資金・回転期間前提 ====================

class WorkingCapitalAssumption(Base):
    """運転資金前提テーブル"""
    __tablename__ = 'working_capital_assumptions'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 回転期間（月）
    cash_turnover_period = Column(Numeric(10, 4))  # 現預金回転期間
    receivables_turnover_period = Column(Numeric(10, 4))  # 売掛債権回転期間
    inventory_turnover_period = Column(Numeric(10, 4))  # 棚卸資産回転期間
    payables_turnover_period = Column(Numeric(10, 4))  # 買掛債務回転期間
    
    # 運転資金増減額
    cash_increase = Column(Numeric(15, 2))  # 手許現預金増加額
    receivables_increase = Column(Numeric(15, 2))  # 売掛債権増加額
    inventory_increase = Column(Numeric(15, 2))  # 棚卸資産増加額
    payables_increase = Column(Numeric(15, 2))  # 買掛債務増加額
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company")
    fiscal_year = relationship("FiscalYear")


class DebtRepaymentAssumption(Base):
    """返済スケジュール前提テーブル"""
    __tablename__ = 'debt_repayment_assumptions'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 借入金明細
    beginning_balance = Column(Numeric(15, 2))  # 借入金期首残高
    borrowing_amount = Column(Numeric(15, 2))  # 借入金借入額
    principal_repayment = Column(Numeric(15, 2))  # 借入金元本返済額
    ending_balance = Column(Numeric(15, 2))  # 借入金期末残高
    interest_payment = Column(Numeric(15, 2))  # 支払利息
    average_interest_rate = Column(Numeric(10, 6))  # 平均金利
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # リレーション
    company = relationship("Company")
    fiscal_year = relationship("FiscalYear")


# ==================== 資金繰り計画（月次） ====================

class MonthlyCashFlowPlan(Base):
    """資金繰り計画の月次データ"""
    __tablename__ = 'monthly_cash_flow_plans'
    
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id'), nullable=False)
    month = Column(Integer, nullable=False, comment='月（1〜12）')
    
    # 月初残高
    beginning_balance = Column(Numeric(15, 2), comment='月初残高')
    
    # （１）手許現預金
    cash = Column(Numeric(15, 2), comment='現金')
    ordinary_deposit_1 = Column(Numeric(15, 2), comment='普通預金1')
    ordinary_deposit_2 = Column(Numeric(15, 2), comment='普通預金2')
    ordinary_deposit_3 = Column(Numeric(15, 2), comment='普通預金3')
    cash_and_deposits_total = Column(Numeric(15, 2), comment='手許現預金計')
    
    # （２）運用預金
    time_deposit = Column(Numeric(15, 2), comment='定期預金')
    investment_deposits_total = Column(Numeric(15, 2), comment='運用預金計')
    
    # 収入
    cash_sales = Column(Numeric(15, 2), comment='現金売上')
    accounts_receivable_collection = Column(Numeric(15, 2), comment='売掛金回収')
    notes_receivable_collection = Column(Numeric(15, 2), comment='手形回収')
    notes_discount = Column(Numeric(15, 2), comment='手形割引')
    other_cash_income = Column(Numeric(15, 2), comment='その他現金収入')
    income_total = Column(Numeric(15, 2), comment='収入計')
    
    # 仕入
    cash_purchases = Column(Numeric(15, 2), comment='現金仕入')
    accounts_payable_payment = Column(Numeric(15, 2), comment='買掛金支払')
    notes_payable_payment = Column(Numeric(15, 2), comment='手形支払')
    other_cash_expenses = Column(Numeric(15, 2), comment='その他現金支出')
    purchases_total = Column(Numeric(15, 2), comment='仕入計')
    
    # 人件費
    executive_compensation = Column(Numeric(15, 2), comment='役員報酬')
    executive_statutory_welfare = Column(Numeric(15, 2), comment='役員法定福利費')
    executive_retirement = Column(Numeric(15, 2), comment='役員退職金')
    salaries = Column(Numeric(15, 2), comment='給料手当')
    temporary_wages = Column(Numeric(15, 2), comment='雑給')
    bonuses = Column(Numeric(15, 2), comment='賞与')
    employee_statutory_welfare = Column(Numeric(15, 2), comment='従業員法定福利費')
    employee_retirement = Column(Numeric(15, 2), comment='従業員退職金')
    welfare_expenses = Column(Numeric(15, 2), comment='福利厚生費')
    labor_cost_total = Column(Numeric(15, 2), comment='人件費計')
    
    # その他経費
    office_supplies = Column(Numeric(15, 2), comment='事務用品費')
    consumables = Column(Numeric(15, 2), comment='消耗品費')
    travel_expenses = Column(Numeric(15, 2), comment='旅費交通費')
    commission_fees = Column(Numeric(15, 2), comment='支払手数料')
    entertainment_expenses = Column(Numeric(15, 2), comment='接待交際費')
    insurance_premiums = Column(Numeric(15, 2), comment='支払保険料')
    communication_expenses = Column(Numeric(15, 2), comment='通信費')
    membership_fees = Column(Numeric(15, 2), comment='諸会費')
    vehicle_expenses = Column(Numeric(15, 2), comment='車両費')
    books_and_publications = Column(Numeric(15, 2), comment='新聞図書費')
    advertising_expenses = Column(Numeric(15, 2), comment='広告宣伝費')
    utilities = Column(Numeric(15, 2), comment='水道光熱費')
    rent = Column(Numeric(15, 2), comment='地代家賃')
    repairs = Column(Numeric(15, 2), comment='修繕費')
    lease_expenses = Column(Numeric(15, 2), comment='賃借料(リース料）')
    miscellaneous_expenses = Column(Numeric(15, 2), comment='雑費')
    other_expenses_total = Column(Numeric(15, 2), comment='その他経費計')
    
    # 経費以外支出
    marketable_securities = Column(Numeric(15, 2), comment='有価証券')
    tangible_fixed_assets = Column(Numeric(15, 2), comment='有形固定資産')
    intangible_fixed_assets = Column(Numeric(15, 2), comment='無形固定資産')
    investments_and_other_assets = Column(Numeric(15, 2), comment='投資その他の資産')
    deferred_assets = Column(Numeric(15, 2), comment='繰延資産')
    non_operating_expenses_total = Column(Numeric(15, 2), comment='経費以外支出計')
    
    # 支出計
    expenses_total = Column(Numeric(15, 2), comment='支出計')
    
    # 差引計（収入－支出）
    net_cash_flow = Column(Numeric(15, 2), comment='差引計（収入－支出）')
    
    # ①月末残高
    ending_balance = Column(Numeric(15, 2), comment='①月末残高')
    
    # ②月末残高－主要運転資金計画
    ending_balance_minus_working_capital = Column(Numeric(15, 2), comment='②月末残高－主要運転資金計画')
    
    # （１）手許現預金（月末）
    ending_cash = Column(Numeric(15, 2), comment='現金（月末）')
    ending_ordinary_deposit_1 = Column(Numeric(15, 2), comment='普通預金1（月末）')
    ending_ordinary_deposit_2 = Column(Numeric(15, 2), comment='普通預金2（月末）')
    ending_ordinary_deposit_3 = Column(Numeric(15, 2), comment='普通預金3（月末）')
    ending_cash_and_deposits_total = Column(Numeric(15, 2), comment='手許現預金計（月末）')
    
    # （２）運用預金（月末）
    ending_time_deposit = Column(Numeric(15, 2), comment='定期預金（月末）')
    ending_investment_deposits_total = Column(Numeric(15, 2), comment='運用預金計（月末）')
    
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    def __repr__(self):
        return f"<MonthlyCashFlowPlan(id={self.id}, company_id={self.company_id}, fiscal_year_id={self.fiscal_year_id}, month={self.month})>"
