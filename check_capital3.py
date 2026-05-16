import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue

db = SessionLocal()
try:
    item = db.query(BsAccountItem).filter_by(id=184).first()
    if item:
        print(f"id={item.id}, account_name={item.account_name}, target_field={item.target_field}, target_statement={item.target_statement}, mapping_status={item.mapping_status}, major_category={item.major_category}")
        svs = db.query(BsStatementValue).filter_by(account_item_id=item.id).all()
        for sv in svs:
            print(f"  -> fiscal_year_id={sv.fiscal_year_id}, amount={sv.amount}")
    else:
        print("id=184 が見つかりません")
finally:
    db.close()
