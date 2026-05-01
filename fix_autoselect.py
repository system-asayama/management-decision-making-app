"""
各分析ページの自動選択JSのselectのidを正しいものに修正するスクリプト
"""

# (ファイル名, 正しいselectのid)
FIXES = [
    ('dashboard_analysis.html',          'company_id'),
    ('simulation.html',                  'company_id'),
    ('retained_earnings_simulation.html','company_select'),
    ('contribution_analysis.html',       'company_select'),
    ('least_squares_forecast.html',      'company_select'),
]

BASE = 'app/templates/'

for fname, correct_id in FIXES:
    fpath = BASE + fname
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 自動選択JSブロック内のgetElementByIdを修正
    import re
    # URLパラメータから企業を自動選択ブロックを探して修正
    pattern = r"(// ===== URLパラメータから企業を自動選択 =====.*?document\.getElementById\(')[^']+('\))"
    replacement = r"\g<1>" + correct_id + r"\g<2>"
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'FIXED: {fname} -> id="{correct_id}"')
    else:
        print(f'NO CHANGE: {fname}')
