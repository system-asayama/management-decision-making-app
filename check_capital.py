import sys, os, json
os.chdir('/app')
sys.path.insert(0, '/app')
from app.db import SessionLocal
from app.models_decision import OriginalTrialBalance, FiscalYear, BsAccountItem, Company

db = SessionLocal()
try:
    tenant_id = 1
    
    # OTBを取得
    latest_otbs = (
        db.query(OriginalTrialBalance)
          .join(FiscalYear, OriginalTrialBalance.fiscal_year_id == FiscalYear.id)
          .join(Company, FiscalYear.company_id == Company.id)
          .filter(Company.tenant_id == tenant_id)
          .order_by(OriginalTrialBalance.updated_at.desc(), OriginalTrialBalance.id.desc())
          .all()
    )
    print(f'OTB count for tenant_id={tenant_id}: {len(latest_otbs)}')
    for otb in latest_otbs[:3]:
        print(f'  OTB id={otb.id} fiscal_year_id={otb.fiscal_year_id} bs_items_count={len(json.loads(otb.bs_items)) if otb.bs_items else 0}')
    
    # _ACCOUNT_SECTION_NAMES
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
    
    # _FIXED_SUMMARY_ACCOUNT_NAMES
    def _normalize(s):
        return s.replace('　', '').replace(' ', '').replace('・', '').lower()
    
    # 最新のOTBのbs_itemsを確認
    if latest_otbs:
        otb = latest_otbs[0]
        if otb.bs_items:
            items = json.loads(otb.bs_items)
            for item in items:
                name = str(item.get('name') or item.get('account_name') or '').strip()
                if '資本金' in name:
                    in_section = name in _ACCOUNT_SECTION_NAMES
                    print(f'  name={name!r} in_SECTION_NAMES={in_section}')
    
    # DBの「資本金」を確認
    capital_item = db.query(BsAccountItem).filter_by(tenant_id=tenant_id, account_name='資本金').first()
    print(f'DB 資本金: {capital_item}')
    
    # 全BsAccountItemを確認
    all_items = db.query(BsAccountItem).filter_by(tenant_id=tenant_id).all()
    print(f'Total BsAccountItems for tenant_id={tenant_id}: {len(all_items)}')
    for item in all_items:
        if '資本' in item.account_name:
            print(f'  id={item.id} name={item.account_name!r} target_field={item.target_field} mapping_status={item.mapping_status}')
finally:
    db.close()
