import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')

from app.db import SessionLocal
from app.models_decision import PlAccountItem, OriginalTrialBalance
import json

db = SessionLocal()
try:
    # 「給与手当」がDBに存在するか確認
    item = db.query(PlAccountItem).filter(
        PlAccountItem.tenant_id == 1,
        PlAccountItem.account_name == '給与手当'
    ).first()
    if item:
        print(f"給与手当 found: id={item.id}, mapping_status={item.mapping_status}, pl_field={item.pl_field}")
    else:
        print("給与手当: DBに存在しない")
    
    # 全OTBのpl_itemsを確認
    otbs = db.query(OriginalTrialBalance).filter(OriginalTrialBalance.tenant_id == 1).all()
    print(f"\n全OTB数: {len(otbs)}")
    for otb in otbs:
        if otb.pl_items:
            try:
                items = json.loads(otb.pl_items)
                names = [i.get('name', '') for i in items if isinstance(i, dict)]
                if '給与手当' in names:
                    print(f"  OTB id={otb.id}, fiscal_year_id={otb.fiscal_year_id}: 給与手当あり")
                else:
                    print(f"  OTB id={otb.id}, fiscal_year_id={otb.fiscal_year_id}: 給与手当なし (pl_items count={len(items)})")
            except Exception as e:
                print(f"  OTB id={otb.id}: parse error {e}")
        else:
            print(f"  OTB id={otb.id}: pl_items=None")
finally:
    db.close()
