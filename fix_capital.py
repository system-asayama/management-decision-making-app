import os, sys
sys.path.insert(0, '/app')
os.chdir('/app')
from app.db import SessionLocal
from app.models_decision import BsAccountItem, BsStatementValue, OriginalTrialBalance
import json

db = SessionLocal()
try:
    tenant_id = 1  # 株式会社ヒカリテックのtenant_id

    # 「資本金合計」をignoredに変更
    capital_sum = db.query(BsAccountItem).filter_by(
        tenant_id=tenant_id, account_name='資本金合計'
    ).first()
    if capital_sum:
        capital_sum.mapping_status = 'ignored'
        capital_sum.target_field = None
        capital_sum.target_statement = None
        print(f"資本金合計 (id={capital_sum.id}) を ignored に変更")

    # 「資本剰余金合計」「利益準備金合計」もignoredに変更
    for name in ['資本剰余金合計', '利益準備金合計']:
        item = db.query(BsAccountItem).filter_by(
            tenant_id=tenant_id, account_name=name
        ).first()
        if item and item.mapping_status not in ('ignored', 'confirmed'):
            item.mapping_status = 'ignored'
            item.target_field = None
            item.target_statement = None
            print(f"{name} (id={item.id}) を ignored に変更")

    # 「資本金」がBsAccountItemに存在しない場合は追加
    existing_capital = db.query(BsAccountItem).filter_by(
        tenant_id=tenant_id, account_name='資本金'
    ).first()
    if not existing_capital:
        new_item = BsAccountItem(
            tenant_id=tenant_id,
            account_name='資本金',
            display_order=80,
            is_auto_created=True,
            major_category='純資産',
            mid_category='資本金',
            sub_category='資本金',
            category_status='confirmed',
            target_statement='BS',
            target_field='capital',
            mapping_status='confirmed',
        )
        db.add(new_item)
        db.flush()
        print(f"資本金 を BsAccountItem に追加 (id={new_item.id})")

        # 各会計年度のBsStatementValueを追加（OTBから金額を取得）
        otbs = db.query(OriginalTrialBalance).all()
        for otb in otbs:
            if not otb.bs_items:
                continue
            try:
                items = json.loads(otb.bs_items)
                for item in items:
                    if isinstance(item, dict) and item.get('name') == '資本金':
                        amount = item.get('amount', 0)
                        sv = BsStatementValue(
                            fiscal_year_id=otb.fiscal_year_id,
                            account_item_id=new_item.id,
                            amount=amount
                        )
                        db.add(sv)
                        print(f"  BsStatementValue 追加: fiscal_year_id={otb.fiscal_year_id}, amount={amount}")
                        break
            except Exception as e:
                print(f"  OTB id={otb.id} エラー: {e}")
    else:
        print(f"資本金 は既に存在 (id={existing_capital.id})")
        # target_fieldが未設定なら設定する
        if not existing_capital.target_field:
            existing_capital.target_statement = 'BS'
            existing_capital.target_field = 'capital'
            existing_capital.mapping_status = 'confirmed'
            print(f"  target_field を capital に設定")

    db.commit()
    print("完了")
finally:
    db.close()
