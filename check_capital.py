from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT id, account_name, tenant_id, target_field, mapping_status "
        "FROM bs_account_items WHERE account_name LIKE :n ORDER BY id"
    ), {'n': '%資本金%'}).fetchall()
    print('count:', len(rows))
    for r in rows:
        print(r)

    # BsStatementValueも確認
    sv_rows = conn.execute(text(
        "SELECT sv.account_item_id, ai.account_name, sv.fiscal_year_id, sv.amount "
        "FROM bs_statement_values sv "
        "JOIN bs_account_items ai ON ai.id = sv.account_item_id "
        "WHERE ai.account_name = :n ORDER BY sv.fiscal_year_id"
    ), {'n': '資本金'}).fetchall()
    print('BsStatementValue for 資本金:', len(sv_rows))
    for r in sv_rows:
        print(r)
