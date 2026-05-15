import sys
import os
sys.path.insert(0, '/app')
os.chdir('/app')

from app.database import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue

db = SessionLocal()
try:
    # capital target_fieldを持つ科目を確認
    items = db.query(BsAccountItem).filter(BsAccountItem.target_field == 'capital').all()
    print(f'capital items count: {len(items)}')
    for i in items:
        print(f'  id={i.id} name={i.account_name} tenant_id={i.tenant_id} mapping_status={i.mapping_status}')
        vals = db.query(BsStatementValue).filter(
            BsStatementValue.account_item_id == i.id,
            BsStatementValue.fiscal_year_id == 34
        ).all()
        for v in vals:
            print(f'    fy34 amount={v.amount}')

    # tenant_id=34のBsAccountItemでtarget_fieldが設定されているものを確認
    print('\n--- tenant_id=34 の全マッピング済み科目 ---')
    items34 = db.query(BsAccountItem).filter(
        BsAccountItem.tenant_id == 34,
        BsAccountItem.target_field.isnot(None),
        BsAccountItem.target_field != ''
    ).all()
    print(f'count: {len(items34)}')
    for i in items34:
        print(f'  {i.account_name} -> {i.target_field} (mapping_status={i.mapping_status})')

    # bs_auto_fillと同じJOINクエリ
    print('\n--- bs_auto_fill JOINクエリ (tenant_id=34, fy=34) ---')
    q = (
        db.query(BsAccountItem, BsStatementValue)
        .join(BsStatementValue,
              (BsStatementValue.account_item_id == BsAccountItem.id) &
              (BsStatementValue.fiscal_year_id == 34))
        .filter(
            BsAccountItem.target_field.isnot(None),
            BsAccountItem.target_field != '',
            BsAccountItem.tenant_id == 34
        )
    )
    rows = q.all()
    print(f'count: {len(rows)}')
    for ai, sv in rows:
        print(f'  {ai.account_name} -> {ai.target_field}: {sv.amount}')
finally:
    db.close()
