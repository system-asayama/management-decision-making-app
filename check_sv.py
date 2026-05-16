import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import PlAccountItem, PlStatementValue

db = SessionLocal()
try:
    # 給与手当・給料手当のPlAccountItemを確認
    items = db.query(PlAccountItem).filter(
        PlAccountItem.account_name.in_(['給与手当', '給料手当'])
    ).all()
    print("=== PlAccountItem ===")
    for item in items:
        print(f"  id={item.id}, tenant_id={item.tenant_id}, account_name={item.account_name}, target_field={item.target_field}, mapping_status={item.mapping_status}")
        # PlStatementValueを確認
        svs = db.query(PlStatementValue).filter(PlStatementValue.account_item_id == item.id).all()
        for sv in svs:
            print(f"    -> PlStatementValue: id={sv.id}, fiscal_year_id={sv.fiscal_year_id}, amount={sv.amount}")
finally:
    db.close()
