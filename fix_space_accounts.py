import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')

from app.db import SessionLocal
from app.models_decision import PlAccountItem, BsAccountItem, McrAccountItem, PlStatementValue, BsStatementValue, McrStatementValue

db = SessionLocal()
try:
    deleted_pl = 0
    deleted_bs = 0
    deleted_mcr = 0

    # PL: スペース入り科目を削除（対応するStatementValueも削除）
    pl_items = db.query(PlAccountItem).all()
    for item in pl_items:
        if ' ' in item.account_name or '\u3000' in item.account_name:
            # 対応するStatementValueを削除
            db.query(PlStatementValue).filter_by(account_item_id=item.id).delete()
            db.delete(item)
            deleted_pl += 1
            print(f"[PL削除] id={item.id}, name='{item.account_name}'")

    # BS: スペース入り科目を削除
    bs_items = db.query(BsAccountItem).all()
    for item in bs_items:
        if ' ' in item.account_name or '\u3000' in item.account_name:
            db.query(BsStatementValue).filter_by(account_item_id=item.id).delete()
            db.delete(item)
            deleted_bs += 1
            print(f"[BS削除] id={item.id}, name='{item.account_name}'")

    # MCR: スペース入り科目を削除
    mcr_items = db.query(McrAccountItem).all()
    for item in mcr_items:
        if ' ' in item.account_name or '\u3000' in item.account_name:
            db.query(McrStatementValue).filter_by(account_item_id=item.id).delete()
            db.delete(item)
            deleted_mcr += 1
            print(f"[MCR削除] id={item.id}, name='{item.account_name}'")

    db.commit()
    print(f"\n完了: PL={deleted_pl}件, BS={deleted_bs}件, MCR={deleted_mcr}件 削除")

except Exception as e:
    db.rollback()
    print(f"エラー: {e}")
    raise
finally:
    db.close()
