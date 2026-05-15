import sys
import os
os.chdir('/app')
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue

db = SessionLocal()
try:
    # 全BsAccountItemのtenant_idの分布を確認
    from sqlalchemy import func
    tenant_counts = db.query(BsAccountItem.tenant_id, func.count(BsAccountItem.id)).group_by(BsAccountItem.tenant_id).all()
    print('=== BsAccountItem tenant_id distribution ===')
    for tid, cnt in tenant_counts:
        print(f'  tenant_id={tid}: {cnt} items')

    # BsStatementValueのfiscal_year_id=34のaccount_item_idを確認
    svs = db.query(BsStatementValue).filter(BsStatementValue.fiscal_year_id == 34).limit(5).all()
    print('\n=== BsStatementValue fy=34 (first 5) ===')
    for sv in svs:
        ai = db.query(BsAccountItem).filter(BsAccountItem.id == sv.account_item_id).first()
        if ai:
            print(f'  ai.id={ai.id} name={ai.account_name} tenant_id={ai.tenant_id} target_field={ai.target_field} amount={sv.amount}')

    # capital target_fieldを持つ科目を確認（全tenant）
    items = db.query(BsAccountItem).filter(BsAccountItem.target_field == 'capital').all()
    print(f'\n=== capital target_field items (all tenants): {len(items)} ===')
    for i in items:
        print(f'  id={i.id} name={i.account_name} tenant_id={i.tenant_id} mapping_status={i.mapping_status}')
        vals = db.query(BsStatementValue).filter(
            BsStatementValue.account_item_id == i.id,
            BsStatementValue.fiscal_year_id == 34
        ).all()
        for v in vals:
            print(f'    fy34 amount={v.amount}')
finally:
    db.close()
