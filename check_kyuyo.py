import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import PlAccountItem, OriginalTrialBalance, FiscalYear, Company
import json
db = SessionLocal()
try:
    # OTB id=67 の詳細を確認
    otb67 = db.query(OriginalTrialBalance).filter(OriginalTrialBalance.id == 67).first()
    if otb67:
        fy = db.query(FiscalYear).filter(FiscalYear.id == otb67.fiscal_year_id).first()
        company = db.query(Company).filter(Company.id == fy.company_id).first() if fy else None
        print(f"=== OTB id=67 ===")
        print(f"  fiscal_year_id={otb67.fiscal_year_id}")
        if fy:
            print(f"  FiscalYear: id={fy.id}, year_name={fy.year_name}, company_id={fy.company_id}")
        if company:
            print(f"  Company: id={company.id}, name={company.name}, tenant_id={company.tenant_id}")
        if otb67.pl_items:
            items = json.loads(otb67.pl_items)
            for i in items:
                if isinstance(i, dict) and '給与' in i.get('name', ''):
                    print(f"  給与関連: {i}")
    
    # 「給与手当」がDBに存在するか確認
    item = db.query(PlAccountItem).filter(
        PlAccountItem.tenant_id == 1,
        PlAccountItem.account_name == '給与手当'
    ).first()
    if item:
        print(f"\n給与手当 found: id={item.id}, mapping_status={item.mapping_status}, target_field={item.target_field}")
    else:
        print("給与手当: DBに存在しない")
finally:
    db.close()
