import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')

from app.db import SessionLocal
from app.models_decision import PlAccountItem, BsAccountItem, McrAccountItem
from collections import defaultdict

db = SessionLocal()
try:
    # PLの重複確認
    pl_items = db.query(PlAccountItem).all()
    pl_by_name = defaultdict(list)
    for item in pl_items:
        pl_by_name[item.account_name].append(item)
    
    print("=== PL重複科目 ===")
    dup_count = 0
    for name, items in sorted(pl_by_name.items()):
        if len(items) > 1:
            dup_count += 1
            print(f"  [{dup_count}] '{name}' x{len(items)}")
            for item in items:
                print(f"      id={item.id}, tenant_id={item.tenant_id}, status={item.mapping_status}, target={item.target_field}")
    
    print(f"\n合計PL科目数: {len(pl_items)}, 重複グループ数: {dup_count}")
    
    # スペース入り科目名の確認
    print("\n=== スペースを含む科目名 (PL) ===")
    space_count = 0
    for item in pl_items:
        if ' ' in item.account_name or '\u3000' in item.account_name:
            space_count += 1
            print(f"  id={item.id}, name='{item.account_name}', status={item.mapping_status}")
    print(f"スペース含む科目数: {space_count}")

finally:
    db.close()
