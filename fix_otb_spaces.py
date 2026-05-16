import os, sys, json, re
sys.path.insert(0, '/app')
os.chdir('/app')

from app.db import SessionLocal
from app.models_decision import OriginalTrialBalance

db = SessionLocal()

def remove_spaces(name: str) -> str:
    """科目名の文字間スペースを除去する（例：「給 料 手 当」→「給料手当」）"""
    if not name:
        return name
    # 全角・半角スペースを除去
    return re.sub(r'[\s\u3000]+', '', name)

def fix_items(items):
    """pl_items/bs_items/mcr_itemsのname/sectionのスペースを除去する"""
    if not items:
        return items, False
    changed = False
    for item in items:
        if isinstance(item, dict):
            old_name = item.get('name', '')
            new_name = remove_spaces(old_name)
            if old_name != new_name:
                item['name'] = new_name
                changed = True
    return items, changed

try:
    otbs = db.query(OriginalTrialBalance).all()
    total_changed = 0
    for otb in otbs:
        modified = False

        if otb.pl_items:
            items = otb.pl_items if isinstance(otb.pl_items, list) else json.loads(otb.pl_items)
            items, ch = fix_items(items)
            if ch:
                otb.pl_items = items
                modified = True

        if otb.bs_items:
            items = otb.bs_items if isinstance(otb.bs_items, list) else json.loads(otb.bs_items)
            items, ch = fix_items(items)
            if ch:
                otb.bs_items = items
                modified = True

        if hasattr(otb, 'mcr_items') and otb.mcr_items:
            items = otb.mcr_items if isinstance(otb.mcr_items, list) else json.loads(otb.mcr_items)
            items, ch = fix_items(items)
            if ch:
                otb.mcr_items = items
                modified = True

        if modified:
            db.add(otb)
            total_changed += 1
            print(f"[修正] OTB id={otb.id}")

    db.commit()
    print(f"\n完了: {total_changed}件のOTBを修正しました")

except Exception as e:
    db.rollback()
    print(f"エラー: {e}")
    import traceback; traceback.print_exc()
finally:
    db.close()
