"""
各分析ページの </script> 直前に、URLのcompany_idパラメータを読み取って
企業選択ドロップダウンを自動設定するJavaScriptを追加するスクリプト
"""
import re

# ページごとの設定: (テンプレートファイル, 企業selectのid, 会計年度selectのid, change発火方法)
PAGES = [
    # (ファイル名, company_select_id, fy_select_id, trigger_change)
    ('breakeven_analysis.html',         'companySelect',   'fiscalYearSelect',    True),
    ('financial_analysis_detailed.html','companySelect',   'fiscalYearSelect',    True),
    ('simulation.html',                 'company_id',      'base_fiscal_year_id', True),
    ('budget_management.html',          'companySelect',   'fiscalYearSelect',    True),
    ('debt_capacity_analysis.html',     'companySelect',   'fiscalYearSelect',    True),
    ('cash_flow_planning.html',         'companySelect',   None,                  True),
    ('retained_earnings_simulation.html','company_select', 'fiscal_year_select',  True),
    ('contribution_analysis.html',      'company_select',  'fiscal_year_select',  True),
    ('differential_cost_analysis.html', 'companySelect',   'fiscalYearSelect',    True),
    ('capital_investment_planning.html','companySelect',   'fiscalYearSelect',    True),
    ('working_capital_planning.html',   'companySelect',   'fiscalYearSelect',    True),
    ('least_squares_forecast.html',     'company_select',  None,                  True),
    ('financing_repayment_planning.html','companySelect',  'fiscalYearSelect',    True),
    ('labor_cost_planning.html',        'companySelect',   'fiscalYearSelect',    True),
    ('dashboard_analysis.html',         'companySelect',   'fiscalYearSelect',    True),
]

JS_TEMPLATE = """
// ===== URLパラメータから企業を自動選択 =====
document.addEventListener('DOMContentLoaded', function() {{
    const params = new URLSearchParams(window.location.search);
    const companyId = params.get('company_id');
    if (companyId) {{
        const sel = document.getElementById('{company_sel}');
        if (sel) {{
            sel.value = companyId;
            // changeイベントを発火して会計年度を自動読み込み
            sel.dispatchEvent(new Event('change'));
        }}
    }}
}});
"""

BASE = 'app/templates/'

for fname, company_sel, fy_sel, trigger in PAGES:
    fpath = BASE + fname
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f'SKIP (not found): {fname}')
        continue

    # すでに自動選択コードが入っている場合はスキップ
    if 'URLパラメータから企業を自動選択' in content:
        print(f'SKIP (already patched): {fname}')
        continue

    # 最後の </script> の直前に挿入
    js_code = JS_TEMPLATE.format(company_sel=company_sel)
    # 最後の </script> を探して挿入
    last_script_pos = content.rfind('</script>')
    if last_script_pos == -1:
        print(f'SKIP (no </script>): {fname}')
        continue

    new_content = content[:last_script_pos] + js_code + content[last_script_pos:]
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'PATCHED: {fname}')
