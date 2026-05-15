import sys
import os
os.chdir('/app')
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue

db = SessionLocal()
try:
    # tenant_id=1の全科目とtarget_fieldを確認
    items = db.query(BsAccountItem).filter(BsAccountItem.tenant_id == 1).all()
    print(f'=== tenant_id=1 の全BsAccountItem ({len(items)}件) ===')
    for i in items:
        if i.target_field:
            print(f'  id={i.id} name={i.account_name} target_field={i.target_field} mapping_status={i.mapping_status}')
        else:
            print(f'  id={i.id} name={i.account_name} target_field=None/empty mapping_status={i.mapping_status}')
finally:
    db.close()
