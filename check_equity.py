import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue

db = SessionLocal()
try:
    # 純資産関連のtarget_fieldを持つBsAccountItemを確認
    equity_fields = ['capital', 'capital_surplus', 'retained_earnings', 'legal_reserve_bs', 'voluntary_reserve_bs', 'retained_earnings_carried', 'treasury_stock']
    
    print("=== 純資産関連のBsAccountItem ===")
    items = db.query(BsAccountItem).filter(
        BsAccountItem.target_field.in_(equity_fields)
    ).all()
    for item in items:
        print(f"  id={item.id}, name='{item.account_name}', target_field='{item.target_field}', status='{item.mapping_status}'")
    
    print("\n=== 利益準備金・任意積立金・繰越利益剰余金のBsAccountItem（名前で検索）===")
    keywords = ['利益準備金', '任意積立金', '繰越利益剰余金', '配当平均積立金', '別途積立金']
    for kw in keywords:
        items2 = db.query(BsAccountItem).filter(BsAccountItem.account_name.like(f'%{kw}%')).all()
        for item in items2:
            print(f"  id={item.id}, name='{item.account_name}', target_field='{item.target_field}', status='{item.mapping_status}'")
    
    print("\n=== fiscal_year_id=34のBsStatementValue（純資産関連）===")
    svs = (db.query(BsStatementValue, BsAccountItem)
           .join(BsAccountItem, BsStatementValue.account_item_id == BsAccountItem.id)
           .filter(BsStatementValue.fiscal_year_id == 34)
           .filter(BsAccountItem.target_field.in_(equity_fields))
           .all())
    for sv, ai in svs:
        print(f"  sv.id={sv.id}, name='{ai.account_name}', target_field='{ai.target_field}', amount={sv.amount}")

finally:
    db.close()
