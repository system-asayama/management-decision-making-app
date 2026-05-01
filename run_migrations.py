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
            ('inventory_assets', 'BIGINT DEFAULT 0 NOT NULL'),
            ('other_current_assets', 'BIGINT DEFAULT 0 NOT NULL'),
            ('quick_assets', 'BIGINT DEFAULT 0 NOT NULL'),
            ('land', 'BIGINT DEFAULT 0 NOT NULL'),
            ('buildings_and_attached', 'BIGINT DEFAULT 0 NOT NULL'),
            ('machinery_and_equipment', 'BIGINT DEFAULT 0 NOT NULL'),
            ('vehicles', 'BIGINT DEFAULT 0 NOT NULL'),
            ('tools_furniture', 'BIGINT DEFAULT 0 NOT NULL'),
            ('other_tangible', 'BIGINT DEFAULT 0 NOT NULL'),
            ('tangible_fixed_assets', 'BIGINT DEFAULT 0 NOT NULL'),
            ('intangible_fixed_assets', 'INTEGER DEFAULT 0 NOT NULL'),
            ('investments_and_other', 'INTEGER DEFAULT 0 NOT NULL'),
            ('deferred_assets', 'INTEGER DEFAULT 0 NOT NULL'),
            ('trade_payables', 'INTEGER DEFAULT 0 NOT NULL'),
            ('short_term_borrowings', 'INTEGER DEFAULT 0 NOT NULL'),
            ('current_portion_long_term', 'INTEGER DEFAULT 0 NOT NULL'),
            ('discounted_notes', 'INTEGER DEFAULT 0 NOT NULL'),
            ('income_taxes_payable', 'BIGINT DEFAULT 0 NOT NULL'),
            ('bonus_reserve', 'BIGINT DEFAULT 0 NOT NULL'),
            ('other_allowances', 'BIGINT DEFAULT 0 NOT NULL'),
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
        
        # マイグレーション: 科目マスタテーブルのcompany_id → tenant_id 変更
        print("\n[マイグレーション] 科目マスタテーブルのtenant_idカラム追加...")
        
        account_tables = ['pl_account_items', 'bs_account_items', 'mcr_account_items']
        for table in account_tables:
            try:
                if _is_pg(conn):
                    # tenant_idカラムの存在確認
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = %s AND column_name = 'tenant_id'
                    """, (table,))
                    if not cur.fetchone():
                        cur.execute(f'ALTER TABLE {table} ADD COLUMN tenant_id INTEGER')
                        conn.commit()
                        # company_idからtenant_idを引き継ぎ
                        cur.execute(f"""
                            UPDATE {table} ai
                            SET tenant_id = c.tenant_id
                            FROM companies c
                            WHERE ai.company_id = c.id
                        """)
                        conn.commit()
                        cur.execute(f'ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL')
                        conn.commit()
                        cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_tenant_id ON {table}(tenant_id)')
                        conn.commit()
                        print(f"  ✅ {table}にtenant_idカラムを追加しました")
                    else:
                        print(f"  ℹ️  {table}.tenant_idは既に存在（スキップ）")
                    # 旧UniqueConstraintを削除して新しいものを追加
                    prefix = table.replace('_account_items', '')
                    old_constraint = f'uq_{prefix}_account_items_company_name'
                    new_constraint = f'uq_{prefix}_account_items_tenant_name'
                    try:
                        cur.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {old_constraint}')
                        conn.commit()
                    except Exception:
                        conn.rollback()
                    try:
                        cur.execute("""
                            SELECT constraint_name FROM information_schema.table_constraints
                            WHERE table_name = %s AND constraint_name = %s
                        """, (table, new_constraint))
                        if not cur.fetchone():
                            cur.execute(f'ALTER TABLE {table} ADD CONSTRAINT {new_constraint} UNIQUE (tenant_id, account_name)')
                            conn.commit()
                            print(f"  ✅ {table}に新UniqueConstraintを追加")
                    except Exception as e2:
                        conn.rollback()
                        print(f"  ⚠️  UniqueConstraint追加スキップ: {e2}")
                else:
                    # SQLiteはテスト環境のみ想定、スキップ
                    print(f"  ℹ️  SQLite環境はスキップ")
            except Exception as e:
                print(f"  ⚠️  {table}マイグレーションエラー: {e}")
                conn.rollback()
        
        # 区分項目（合計・小計・利益・損失など）を科目マスタから削除
        print("\n[マイグレーション] 科目マスタの区分項目クリーンアップ...")
        try:
            if _is_pg(conn):
                # 会計システムの大分類・中分類・小分類名（区分名）のリスト
                section_names = (
                    '資産', '負債', '純資産', '損益', '収益', '費用', '口座',
                    '流動資産', '固定資産', '繰延資産',
                    '流動負債', '固定負債',
                    '資本金', '資本剰余金', '利益剰余金', '自己株式', '評価換算差額等', '新株予約権',
                    '売上高', '売上原価', '販売費及び一般管理費', '営業外収益', '営業外費用', '特別利益', '特別損失', '法人税等',
                    '現金及び預金', '売上債権', '棚卸資産', '有価証券', '投資その他の資産',
                    '有形固定資産', '無形固定資産',
                    '仕入債務', 'その他流動負債', 'その他流動資産',
                    '販売費', '一般管理費', '営業外収益', '営業外費用', '特別利益', '特別損失', '法人税等',
                    '販管費',
                )
                placeholders = ','.join(["'" + s + "'" for s in section_names])
                for table in ['pl_account_items', 'bs_account_items', 'mcr_account_items']:
                    value_table = table.replace('_account_items', '_statement_values')
                    # 関連する値テーブルも先に削除
                    cur.execute(f"""
                        DELETE FROM {value_table}
                        WHERE account_item_id IN (
                            SELECT id FROM {table}
                            WHERE account_name IN ({placeholders})
                        )
                    """)
                    conn.commit()
                    cur.execute(f"""
                        DELETE FROM {table}
                        WHERE account_name IN ({placeholders})
                    """)
                    conn.commit()
                    print(f"  ✅ {table}の区分項目を削除しました")
            else:
                print("  ℹ️  SQLite環境はスキップ")
        except Exception as e:
            print(f"  ⚠️  区分項目クリーンアップエラー: {e}")
            conn.rollback()

        # 科目マスタに大分類・中分類・小分類・category_statusカラムを追加
        print("\n[マイグレーション] 科目マスタに分類カラムを追加...")
        try:
            if _is_pg(conn):
                for table in ['pl_account_items', 'bs_account_items', 'mcr_account_items']:
                    for col, coltype, default in [
                        ('major_category', 'VARCHAR(50)', None),
                        ('mid_category', 'VARCHAR(100)', None),
                        ('sub_category', 'VARCHAR(100)', None),
                        ('category_status', "VARCHAR(20) DEFAULT 'uncategorized' NOT NULL", None),
                    ]:
                        try:
                            if default:
                                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {coltype} DEFAULT '{default}'")
                            else:
                                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {coltype}")
                            conn.commit()
                        except Exception as col_e:
                            conn.rollback()
                    print(f"  ✅ {table}に分類カラムを追加しました")
            else:
                print("  ℹ️  SQLite環境はスキップ")
        except Exception as e:
            print(f"  ⚠️  分類カラム追加エラー: {e}")
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
