import sys, os, json
os.chdir('/app')
sys.path.insert(0, '/app')
from app.db import SessionLocal
from app.models_decision import OriginalTrialBalance, FiscalYear, BsAccountItem

db = SessionLocal()
try:
    # _ACCOUNT_SECTION_NAMES（upsert_statement_valuesと同じ定義）
    _ACCOUNT_SECTION_NAMES = {
        '資産', '負債', '純資産', '損益', '収益', '費用', '口座',
        '流動資産', '固定資産', '繰延資産',
        '流動負債', '固定負債',
        '資本剰余金', '利益剰余金', '自己株式', '評価換算差額等', '新株予約権',
        '販売費及び一般管理費',
        '現金及び預金', '売上債権', '棚卸資産', '有価証券', '投資その他の資産',
        '有形固定資産', '無形固定資産',
        '仕入債務', 'その他流動負債', 'その他流動資産',
        '販管費',
    }
    
    print('「資本金」in _ACCOUNT_SECTION_NAMES:', '資本金' in _ACCOUNT_SECTION_NAMES)
    
    # bs_itemsのJSONを確認
    otb = db.query(OriginalTrialBalance).filter_by(fiscal_year_id=34).order_by(OriginalTrialBalance.id.desc()).first()
    if otb and otb.bs_items:
        items = json.loads(otb.bs_items)
        for item in items:
            name = str(item.get('name') or item.get('account_name') or '').strip()
            if name == '資本金':
                print(f'bs_items に「資本金」あり: {item}')
                print(f'  → _ACCOUNT_SECTION_NAMESでスキップ: {name in _ACCOUNT_SECTION_NAMES}')
    
    # DBに「資本金」が存在するか確認
    item = db.query(BsAccountItem).filter_by(tenant_id=1, account_name='資本金').first()
    print(f'DB に「資本金」: {item}')
    if item:
        print(f'  id={item.id} target_field={item.target_field} mapping_status={item.mapping_status}')
finally:
    db.close()
