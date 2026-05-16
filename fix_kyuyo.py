import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import PlAccountItem, OriginalTrialBalance
import json

db = SessionLocal()
try:
    # 1. PlAccountItemの「給与手当」を「給料手当」に修正
    item = db.query(PlAccountItem).filter(
        PlAccountItem.tenant_id == 1,
        PlAccountItem.account_name == '給与手当'
    ).first()
    if item:
        print(f"PlAccountItem修正前: id={item.id}, account_name={item.account_name}, mapping_status={item.mapping_status}, target_field={item.target_field}")
        item.account_name = '給料手当'
        db.flush()
        print(f"PlAccountItem修正後: id={item.id}, account_name={item.account_name}")
    else:
        print("PlAccountItem: 給与手当 not found")
    
    # 2. OriginalTrialBalanceのpl_itemsの「給与手当」を「給料手当」に修正
    otbs = db.query(OriginalTrialBalance).all()
    for otb in otbs:
        if otb.pl_items:
            try:
                items = json.loads(otb.pl_items)
                changed = False
                for i in items:
                    if isinstance(i, dict) and i.get('name') == '給与手当':
                        print(f"OTB id={otb.id}: pl_items内の「給与手当」を「給料手当」に修正")
                        i['name'] = '給料手当'
                        changed = True
                if changed:
                    otb.pl_items = json.dumps(items, ensure_ascii=False)
            except Exception as e:
                print(f"OTB id={otb.id}: parse error {e}")
    
    db.commit()
    print("修正完了")
finally:
    db.close()
