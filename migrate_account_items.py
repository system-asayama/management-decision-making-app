"""
科目マスタテーブルのマイグレーション
company_id → tenant_id への変更

実行方法: python3 migrate_account_items.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal, engine
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        print("=== 科目マスタ マイグレーション開始 ===")
        
        # 1. 既存データの確認
        for table in ['pl_account_items', 'bs_account_items', 'mcr_account_items']:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"{table}: {result}件")
        
        # 2. 各テーブルにtenant_idカラムを追加（company_idからcompany.tenant_idを引き継ぐ）
        for table in ['pl_account_items', 'bs_account_items', 'mcr_account_items']:
            print(f"\n{table} の処理中...")
            
            # カラムが既に存在するか確認
            try:
                db.execute(text(f"SELECT tenant_id FROM {table} LIMIT 1"))
                print(f"  tenant_idカラムは既に存在します")
                has_tenant_id = True
            except Exception:
                db.rollback()
                has_tenant_id = False
            
            if not has_tenant_id:
                # tenant_idカラムを追加
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN tenant_id INT"))
                db.commit()
                print(f"  tenant_idカラムを追加しました")
                
                # company_idからtenant_idを引き継ぐ
                db.execute(text(f"""
                    UPDATE {table} ai
                    JOIN companies c ON ai.company_id = c.id
                    SET ai.tenant_id = c.tenant_id
                """))
                db.commit()
                print(f"  tenant_idをcompany.tenant_idから設定しました")
                
                # NOT NULL制約を追加
                db.execute(text(f"ALTER TABLE {table} MODIFY COLUMN tenant_id INT NOT NULL"))
                db.commit()
                print(f"  NOT NULL制約を追加しました")
                
                # インデックスを追加
                db.execute(text(f"CREATE INDEX idx_{table}_tenant_id ON {table}(tenant_id)"))
                db.commit()
                print(f"  インデックスを追加しました")
            
            # 古いUniqueConstraintを削除して新しいものを追加
            constraint_name_old = f"uq_{table.replace('_account_items', '')}_account_items_company_name"
            constraint_name_new = f"uq_{table.replace('_account_items', '')}_account_items_tenant_name"
            
            try:
                db.execute(text(f"ALTER TABLE {table} DROP INDEX {constraint_name_old}"))
                db.commit()
                print(f"  古いUniqueConstraint({constraint_name_old})を削除しました")
            except Exception as e:
                db.rollback()
                print(f"  古いUniqueConstraint削除スキップ: {e}")
            
            try:
                db.execute(text(f"ALTER TABLE {table} ADD UNIQUE KEY {constraint_name_new} (tenant_id, account_name)"))
                db.commit()
                print(f"  新しいUniqueConstraint({constraint_name_new})を追加しました")
            except Exception as e:
                db.rollback()
                print(f"  新しいUniqueConstraint追加スキップ: {e}")
        
        print("\n=== マイグレーション完了 ===")
        
        # 3. 結果確認
        for table in ['pl_account_items', 'bs_account_items', 'mcr_account_items']:
            result = db.execute(text(f"SELECT COUNT(*), MIN(tenant_id), MAX(tenant_id) FROM {table}")).fetchone()
            print(f"{table}: {result[0]}件, tenant_id範囲: {result[1]}〜{result[2]}")
        
    except Exception as e:
        db.rollback()
        print(f"エラー: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    migrate()
