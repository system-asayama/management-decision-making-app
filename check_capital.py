import sys, os, json
os.chdir('/app')
sys.path.insert(0, '/app')
from app.db import SessionLocal
from app.models_decision import OriginalTrialBalance, FiscalYear, Company

db = SessionLocal()
try:
    # fiscal_year_id=34のOTBを取得
    fy = db.query(FiscalYear).filter_by(id=34).first()
    if not fy:
        print('FiscalYear id=34 not found')
        exit()
    
    otbs = db.query(OriginalTrialBalance).filter_by(fiscal_year_id=34).order_by(OriginalTrialBalance.id.desc()).all()
    print(f'OTB count for fy=34: {len(otbs)}')
    
    for otb in otbs[:1]:  # 最新の1件
        print(f'OTB id={otb.id}')
        if otb.bs_items:
            items = json.loads(otb.bs_items)
            print(f'bs_items count: {len(items)}')
            # 資本金関連を探す
            for item in items:
                name = item.get('name') or item.get('account_name') or ''
                if '資本' in name or '純資産' in name:
                    print(f'  name={name!r} section={item.get("section")!r} amount={item.get("amount")}')
        else:
            print('bs_items is empty')
finally:
    db.close()
