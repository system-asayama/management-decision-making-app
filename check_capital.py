import sys, os
os.chdir('/app')
sys.path.insert(0, '/app')
from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue

db = SessionLocal()
try:
    # 純資産関連の全科目を確認（target_statement='純資産' or account_nameに資本金を含む）
    items = db.query(BsAccountItem).filter(
        BsAccountItem.tenant_id == 1
    ).order_by(BsAccountItem.display_order).all()
    
    print('=== tenant_id=1 の全BSアカウント（純資産関連） ===')
    for i in items:
        if any(k in (i.account_name or '') for k in ['資本', '純資産', '利益', '剰余', '自己株']):
            sv = db.query(BsStatementValue).filter(
                BsStatementValue.account_item_id == i.id,
                BsStatementValue.fiscal_year_id == 34
            ).first()
            amount = sv.amount if sv else None
            print(f'  id={i.id} name={i.account_name!r} target_field={i.target_field!r} mapping_status={i.mapping_status!r} amount={amount}')
finally:
    db.close()
