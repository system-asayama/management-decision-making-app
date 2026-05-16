import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue, OriginalTrialBalance
import json

db = SessionLocal()
try:
    # OTB id=39 (fiscal_year_id=34) のbs_itemsを全て表示
    otb = db.query(OriginalTrialBalance).filter_by(id=39).first()
    if otb and otb.bs_items:
        items = json.loads(otb.bs_items)
        print(f"OTB id=39, fiscal_year_id=34, bs_items count={len(items)}")
        # 純資産セクション付近を表示
        for i, item in enumerate(items):
            name = item.get('name', '')
            if '資本' in name or '純資産' in name or '剰余' in name or '利益準備' in name:
                print(f"  [{i}] {item}")
    
    # BsAccountItemの全レコードを確認（純資産関連）
    print("\n=== BsAccountItem (純資産関連) ===")
    items_db = db.query(BsAccountItem).filter(
        BsAccountItem.major_category == '純資産'
    ).order_by(BsAccountItem.display_order).all()
    for item in items_db:
        print(f"  id={item.id}, account_name={item.account_name}, target_field={item.target_field}, mapping_status={item.mapping_status}")
        svs = db.query(BsStatementValue).filter(BsStatementValue.account_item_id == item.id).all()
        for sv in svs:
            print(f"    -> fiscal_year_id={sv.fiscal_year_id}, amount={sv.amount}")
finally:
    db.close()
