#!/usr/bin/env python3
"""
Heroku releaseフェーズで実行されるマイグレーションスクリプト
"""
import os
import sys

# アプリケーションのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.db import get_db_connection, _is_pg

def run_migrations():
    """マイグレーションを実行"""
    print("=" * 60)
    print("マイグレーション開始")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # マイグレーション1: T_管理者テーブルにactiveカラムを追加
        print("\n[マイグレーション] T_管理者テーブルにactiveカラムを追加...")
        
        try:
            if _is_pg(conn):
                # PostgreSQL: カラムが存在するか確認
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'T_管理者' AND column_name = 'active'
                """)
                if not cur.fetchone():
                    print("  - activeカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_管理者" ADD COLUMN active INTEGER DEFAULT 1')
                    cur.execute('UPDATE "T_管理者" SET active = 1 WHERE active IS NULL')
                    conn.commit()
                    print("  ✅ T_管理者テーブルにactiveカラムを追加しました")
                else:
                    print("  ℹ️  activeカラムは既に存在します（スキップ）")
            else:
                # SQLite: PRAGMAでカラムを確認
                cur.execute('PRAGMA table_info("T_管理者")')
                columns = [row[1] for row in cur.fetchall()]
                if 'active' not in columns:
                    print("  - activeカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_管理者" ADD COLUMN active INTEGER DEFAULT 1')
                    cur.execute('UPDATE "T_管理者" SET active = 1 WHERE active IS NULL')
                    conn.commit()
                    print("  ✅ T_管理者テーブルにactiveカラムを追加しました")
                else:
                    print("  ℹ️  activeカラムは既に存在します（スキップ）")
        except Exception as e:
            print(f"  ⚠️  マイグレーションエラー: {e}")
            conn.rollback()
            raise
        
        # マイグレーション2: T_従業員テーブルにactiveカラムを追加
        print("\n[マイグレーション] T_従業員テーブルにactiveカラムを追加...")
        
        try:
            if _is_pg(conn):
                # PostgreSQL: カラムが存在するか確認
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'T_従業員' AND column_name = 'active'
                """)
                if not cur.fetchone():
                    print("  - activeカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_従業員" ADD COLUMN active INTEGER DEFAULT 1')
                    cur.execute('UPDATE "T_従業員" SET active = 1 WHERE active IS NULL')
                    conn.commit()
                    print("  ✅ T_従業員テーブルにactiveカラムを追加しました")
                else:
                    print("  ℹ️  activeカラムは既に存在します（スキップ）")
            else:
                # SQLite: PRAGMAでカラムを確認
                cur.execute('PRAGMA table_info("T_従業員")')
                columns = [row[1] for row in cur.fetchall()]
                if 'active' not in columns:
                    print("  - activeカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_従業員" ADD COLUMN active INTEGER DEFAULT 1')
                    cur.execute('UPDATE "T_従業員" SET active = 1 WHERE active IS NULL')
                    conn.commit()
                    print("  ✅ T_従業員テーブルにactiveカラムを追加しました")
                else:
                    print("  ℹ️  activeカラムは既に存在します（スキップ）")
        except Exception as e:
            print(f"  ⚠️  マイグレーションエラー: {e}")
            conn.rollback()
            raise
        
        # マイグレーション3: T_テナント管理者_テナントテーブルにcan_manage_tenant_adminsカラムを追加
        print("\n[マイグレーション] T_テナント管理者_テナントテーブルにcan_manage_tenant_adminsカラムを追加...")
        
        try:
            if _is_pg(conn):
                # PostgreSQL: カラムが存在するか確認
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'T_テナント管理者_テナント' AND column_name = 'can_manage_tenant_admins'
                """)
                if not cur.fetchone():
                    print("  - can_manage_tenant_adminsカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_テナント管理者_テナント" ADD COLUMN can_manage_tenant_admins INTEGER DEFAULT 0')
                    conn.commit()
                    print("  ✅ T_テナント管理者_テナントテーブルにcan_manage_tenant_adminsカラムを追加しました")
                else:
                    print("  ℹ️  can_manage_tenant_adminsカラムは既に存在します（スキップ）")
            else:
                # SQLite: PRAGMAでカラムを確認
                cur.execute('PRAGMA table_info("T_テナント管理者_テナント")')
                columns = [row[1] for row in cur.fetchall()]
                if 'can_manage_tenant_admins' not in columns:
                    print("  - can_manage_tenant_adminsカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_テナント管理者_テナント" ADD COLUMN can_manage_tenant_admins INTEGER DEFAULT 0')
                    conn.commit()
                    print("  ✅ T_テナント管理者_テナントテーブルにcan_manage_tenant_adminsカラムを追加しました")
                else:
                    print("  ℹ️  can_manage_tenant_adminsカラムは既に存在します（スキップ）")
        except Exception as e:
            print(f"  ⚠️  マイグレーションエラー: {e}")
            conn.rollback()
            raise
        
        # マイグレーション4: T_管理者テーブルにemailカラムを追加
        print("\n[マイグレーション] T_管理者テーブルにemailカラムを追加...")
        
        try:
            if _is_pg(conn):
                # PostgreSQL: カラムが存在するか確認
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'T_管理者' AND column_name = 'email'
                """)
                if not cur.fetchone():
                    print("  - emailカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_管理者" ADD COLUMN email TEXT')
                    conn.commit()
                    print("  ✅ T_管理者テーブルにemailカラムを追加しました")
                else:
                    print("  ℹ️  emailカラムは既に存在します（スキップ）")
            else:
                # SQLite: PRAGMAでカラムを確認
                cur.execute('PRAGMA table_info("T_管理者")')
                columns = [row[1] for row in cur.fetchall()]
                if 'email' not in columns:
                    print("  - emailカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_管理者" ADD COLUMN email TEXT')
                    conn.commit()
                    print("  ✅ T_管理者テーブルにemailカラムを追加しました")
                else:
                    print("  ℹ️  emailカラムは既に存在します（スキップ）")
        except Exception as e:
            print(f"  ⚠️  マイグレーションエラー: {e}")
            conn.rollback()
            raise
        
        # マイグレーション5: T_管理者テーブルにopenai_api_keyカラムを追加
        print("\n[マイグレーション] T_管理者テーブルにopenai_api_keyカラムを追加...")
        
        try:
            if _is_pg(conn):
                # PostgreSQL: カラムが存在するか確認
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'T_管理者' AND column_name = 'openai_api_key'
                """)
                if not cur.fetchone():
                    print("  - openai_api_keyカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_管理者" ADD COLUMN openai_api_key TEXT DEFAULT NULL')
                    conn.commit()
                    print("  ✅ T_管理者テーブルにopenai_api_keyカラムを追加しました")
                else:
                    print("  ℹ️  openai_api_keyカラムは既に存在します（スキップ）")
            else:
                # SQLite: PRAGMAでカラムを確認
                cur.execute('PRAGMA table_info("T_管理者")')
                columns = [row[1] for row in cur.fetchall()]
                if 'openai_api_key' not in columns:
                    print("  - openai_api_keyカラムが存在しません。追加します...")
                    cur.execute('ALTER TABLE "T_管理者" ADD COLUMN openai_api_key TEXT DEFAULT NULL')
                    conn.commit()
                    print("  ✅ T_管理者テーブルにopenai_api_keyカラムを追加しました")
                else:
                    print("  ℹ️  openai_api_keyカラムは既に存在します（スキップ）")
        except Exception as e:
            print(f"  ⚠️  マイグレーションエラー: {e}")
            conn.rollback()
            raise
        
        # マイグレーション6: T_テナントテーブルに連絡先カラムを追加
        print("\n[マイグレーション] T_テナントテーブルに連絡先カラムを追加...")
        
        contact_columns = [
            ('郵便番号', 'TEXT'),
            ('住所', 'TEXT'),
            ('電話番号', 'TEXT'),
            ('email', 'TEXT'),
            ('openai_api_key', 'TEXT DEFAULT NULL'),
            ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for col_name, col_type in contact_columns:
            try:
                if _is_pg(conn):
                    # PostgreSQL: カラムが存在するか確認
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'T_テナント' AND column_name = %s
                    """, (col_name,))
                    if not cur.fetchone():
                        print(f"  - {col_name}カラムが存在しません。追加します...")
                        cur.execute(f'ALTER TABLE "T_テナント" ADD COLUMN "{col_name}" {col_type}')
                        conn.commit()
                        print(f"  ✅ T_テナントテーブルに{col_name}カラムを追加しました")
                    else:
                        print(f"  ℹ️  {col_name}カラムは既に存在します（スキップ）")
                else:
                    # SQLite: PRAGMAでカラムを確認
                    cur.execute('PRAGMA table_info("T_テナント")')
                    columns = [row[1] for row in cur.fetchall()]
                    if col_name not in columns:
                        print(f"  - {col_name}カラムが存在しません。追加します...")
                        cur.execute(f'ALTER TABLE "T_テナント" ADD COLUMN "{col_name}" {col_type}')
                        conn.commit()
                        print(f"  ✅ T_テナントテーブルに{col_name}カラムを追加しました")
                    else:
                        print(f"  ℹ️  {col_name}カラムは既に存在します（スキップ）")
            except Exception as e:
                print(f"  ⚠️  {col_name}カラムのマイグレーションエラー: {e}")
                conn.rollback()
                raise
        
         # マイグレーション: restructured_plテーブルに新規カラムを追加
        print("\n[マイグレーション] restructured_plテーブルにPL組換え用カラムを追加...")
        
        pl_new_columns = [
            ('beginning_inventory', 'INTEGER DEFAULT 0 NOT NULL'),
            ('manufacturing_cost', 'INTEGER DEFAULT 0 NOT NULL'),
            ('ending_inventory', 'INTEGER DEFAULT 0 NOT NULL'),
            ('external_cost_adjustment', 'INTEGER DEFAULT 0 NOT NULL'),
            ('gross_added_value', 'INTEGER DEFAULT 0 NOT NULL'),
            ('labor_cost', 'INTEGER DEFAULT 0 NOT NULL'),
            ('executive_compensation', 'INTEGER DEFAULT 0 NOT NULL'),
            ('capital_regeneration_cost', 'INTEGER DEFAULT 0 NOT NULL'),
            ('research_development_expenses', 'INTEGER DEFAULT 0 NOT NULL'),
            ('general_expenses', 'INTEGER DEFAULT 0 NOT NULL'),
            ('general_expenses_fixed', 'INTEGER DEFAULT 0 NOT NULL'),
            ('general_expenses_variable', 'INTEGER DEFAULT 0 NOT NULL'),
            ('financial_profit_loss', 'INTEGER DEFAULT 0 NOT NULL'),
            ('other_non_operating', 'INTEGER DEFAULT 0 NOT NULL'),
            ('extraordinary_profit_loss', 'INTEGER DEFAULT 0 NOT NULL'),
            ('dividend', 'INTEGER DEFAULT 0 NOT NULL'),
            ('retained_profit', 'INTEGER DEFAULT 0 NOT NULL'),
            ('legal_reserve', 'INTEGER DEFAULT 0 NOT NULL'),
            ('voluntary_reserve', 'INTEGER DEFAULT 0 NOT NULL'),
            ('retained_earnings_increase', 'INTEGER DEFAULT 0 NOT NULL'),
        ]
        
        for col_name, col_type in pl_new_columns:
            try:
                if _is_pg(conn):
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'restructured_pl' AND column_name = %s
                    """, (col_name,))
                    if not cur.fetchone():
                        cur.execute(f'ALTER TABLE restructured_pl ADD COLUMN {col_name} {col_type}')
                        conn.commit()
                        print(f"  ✅ restructured_plに{col_name}カラムを追加")
                    else:
                        print(f"  ℹ️  {col_name}は既に存在（スキップ）")
                else:
                    cur.execute('PRAGMA table_info(restructured_pl)')
                    columns = [row[1] for row in cur.fetchall()]
                    if col_name not in columns:
                        cur.execute(f'ALTER TABLE restructured_pl ADD COLUMN {col_name} {col_type}')
                        conn.commit()
                        print(f"  ✅ restructured_plに{col_name}カラムを追加")
                    else:
                        print(f"  ℹ️  {col_name}は既に存在（スキップ）")
            except Exception as e:
                print(f"  ⚠️  {col_name}カラム追加エラー: {e}")
                conn.rollback()
        
        # マイグレーション: restructured_bsテーブルに新規カラムを追加
        print("\n[マイグレーション] restructured_bsテーブルにBS組換え用カラムを追加...")
        
        bs_new_columns = [
            ('cash_on_hand', 'INTEGER DEFAULT 0 NOT NULL'),
            ('investment_deposits', 'INTEGER DEFAULT 0 NOT NULL'),
            ('marketable_securities', 'INTEGER DEFAULT 0 NOT NULL'),
            ('trade_receivables', 'INTEGER DEFAULT 0 NOT NULL'),
            ('inventory_assets', 'INTEGER DEFAULT 0 NOT NULL'),
            ('tangible_fixed_assets', 'INTEGER DEFAULT 0 NOT NULL'),
            ('intangible_fixed_assets', 'INTEGER DEFAULT 0 NOT NULL'),
            ('investments_and_other', 'INTEGER DEFAULT 0 NOT NULL'),
            ('deferred_assets', 'INTEGER DEFAULT 0 NOT NULL'),
            ('trade_payables', 'INTEGER DEFAULT 0 NOT NULL'),
            ('short_term_borrowings', 'INTEGER DEFAULT 0 NOT NULL'),
            ('current_portion_long_term', 'INTEGER DEFAULT 0 NOT NULL'),
            ('discounted_notes', 'INTEGER DEFAULT 0 NOT NULL'),
            ('other_current_liabilities', 'INTEGER DEFAULT 0 NOT NULL'),
            ('long_term_borrowings', 'INTEGER DEFAULT 0 NOT NULL'),
            ('executive_borrowings', 'INTEGER DEFAULT 0 NOT NULL'),
            ('retirement_benefit_liability', 'INTEGER DEFAULT 0 NOT NULL'),
            ('other_fixed_liabilities', 'INTEGER DEFAULT 0 NOT NULL'),
            ('capital', 'INTEGER DEFAULT 0 NOT NULL'),
            ('capital_surplus', 'INTEGER DEFAULT 0 NOT NULL'),
            ('legal_reserve_bs', 'INTEGER DEFAULT 0 NOT NULL'),
            ('voluntary_reserve_bs', 'INTEGER DEFAULT 0 NOT NULL'),
            ('retained_earnings_carried', 'INTEGER DEFAULT 0 NOT NULL'),
            ('treasury_stock', 'INTEGER DEFAULT 0 NOT NULL'),
            ('discounted_notes_note', 'INTEGER DEFAULT 0 NOT NULL'),
            ('endorsed_notes_note', 'INTEGER DEFAULT 0 NOT NULL'),
        ]
        
        for col_name, col_type in bs_new_columns:
            try:
                if _is_pg(conn):
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'restructured_bs' AND column_name = %s
                    """, (col_name,))
                    if not cur.fetchone():
                        cur.execute(f'ALTER TABLE restructured_bs ADD COLUMN {col_name} {col_type}')
                        conn.commit()
                        print(f"  ✅ restructured_bsに{col_name}カラムを追加")
                    else:
                        print(f"  ℹ️  {col_name}は既に存在（スキップ）")
                else:
                    cur.execute('PRAGMA table_info(restructured_bs)')
                    columns = [row[1] for row in cur.fetchall()]
                    if col_name not in columns:
                        cur.execute(f'ALTER TABLE restructured_bs ADD COLUMN {col_name} {col_type}')
                        conn.commit()
                        print(f"  ✅ restructured_bsに{col_name}カラムを追加")
                    else:
                        print(f"  ℹ️  {col_name}は既に存在（スキップ）")
            except Exception as e:
                print(f"  ⚠️  {col_name}カラム追加エラー: {e}")
                conn.rollback()
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("マイグレーション完了")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ マイグレーション失敗: {e}")
        print("=" * 60)
        return 1
if __name__ == "__main__":
    sys.exit(run_migrations())
