import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue, OriginalTrialBalance
import json

db = SessionLocal()
try:
    # BsAccountItemで「資本金」を確認
    items = db.query(BsAccountItem).filter(
        BsAccountItem.account_name.like('%資本金%')
    ).all()
    print("=== BsAccountItem (資本金) ===")
    for item in items:
        print(f"  id={item.id}, tenant_id={item.tenant_id}, account_name={item.account_name}, target_field={item.target_field}, mapping_status={item.mapping_status}")
        svs = db.query(BsStatementValue).filter(BsStatementValue.account_item_id == item.id).all()
        for sv in svs:
            print(f"    -> BsStatementValue: id={sv.id}, fiscal_year_id={sv.fiscal_year_id}, amount={sv.amount}")

    # OTBのbs_itemsで「資本金」を確認
    print("\n=== OTB bs_items (資本金) ===")
    otbs = db.query(OriginalTrialBalance).all()
    for otb in otbs:
        if otb.bs_items:
            try:
                items_list = json.loads(otb.bs_items)
                for i in items_list:
                    if isinstance(i, dict) and '資本金' in str(i.get('name', '')):
                        print(f"  OTB id={otb.id}, fiscal_year_id={otb.fiscal_year_id}: {i}")
            except Exception as e:
                pass
finally:
    db.close()
