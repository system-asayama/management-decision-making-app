import sys
import os
os.chdir('/app')
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue

db = SessionLocal()
try:
    # id=80周辺の科目を確認
    items = db.query(BsAccountItem).filter(
        BsAccountItem.tenant_id == 1,
        BsAccountItem.id.between(75, 100)
    ).order_by(BsAccountItem.id).all()
    print('=== id=75-100 の BsAccountItem ===')
    for i in items:
        print(f'  id={i.id} name={i.account_name} target_field={i.target_field} mapping_status={i.mapping_status}')
        vals = db.query(BsStatementValue).filter(
            BsStatementValue.account_item_id == i.id,
            BsStatementValue.fiscal_year_id == 34
        ).all()
        for v in vals:
            print(f'    fy34 amount={v.amount}')

    # display_order順で純資産関連科目
    print('\n=== display_order順で純資産関連科目 ===')
    items_ordered = db.query(BsAccountItem).filter(
        BsAccountItem.tenant_id == 1,
        BsAccountItem.major_category == '純資産'
    ).order_by(BsAccountItem.display_order).all()
    for i in items_ordered:
        print(f'  display_order={i.display_order} id={i.id} name={i.account_name} target_field={i.target_field} mapping_status={i.mapping_status}')
finally:
    db.close()
