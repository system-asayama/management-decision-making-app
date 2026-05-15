import sys, os
os.chdir('/app')
sys.path.insert(0, '/app')
from app.db import SessionLocal
from app.models_decision import BsAccountItem

db = SessionLocal()
try:
    # 「資本金」を含む全科目を確認
    items = db.query(BsAccountItem).filter(
        BsAccountItem.account_name.like('%資本金%')
    ).order_by(BsAccountItem.id).all()
    print('=== 資本金を含む科目 ===')
    for i in items:
        print(f'  id={i.id} tenant_id={i.tenant_id} name={i.account_name} target_field={i.target_field} mapping_status={i.mapping_status}')
finally:
    db.close()
