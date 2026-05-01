#!/usr/bin/env python3
"""
全テンプレートのデザインを統一するスクリプト
1. 個別のBootstrap/FontAwesome読み込みを削除（base.htmlで一括読み込み済み）
2. 旧スタイルのヘッダー（h2タグのみ）をグラデーションカードヘッダーに変換
3. Tailwind CSSクラスをBootstrap5クラスに変換
"""
import re
import os

TEMPLATES_DIR = "app/templates"

# Bootstrap重複読み込みを削除するファイル
REMOVE_BOOTSTRAP_FILES = [
    "account_master.html",
    "pdf_upload.html",
    "financial_statements_view.html",
    "restructuring.html",
]

# ヘッダーをグラデーションカードに変換するファイルと設定
HEADER_UPGRADES = {
    "company_list.html": {
        "icon": "fas fa-building",
        "title": "企業管理",
        "subtitle": "企業情報の登録・管理を行います。",
        "gradient": "linear-gradient(135deg, #0056b3 0%, #007bff 100%)",
        "old_pattern": r'<div class="row mb-4">.*?</div>\s*</div>',
    },
    "company_form.html": {
        "icon": "fas fa-building",
        "gradient": "linear-gradient(135deg, #0056b3 0%, #007bff 100%)",
    },
    "breakeven_analysis.html": {
        "icon": "fas fa-chart-area",
        "title": "損益分岐点分析",
        "subtitle": "損益分岐点売上高・安全余裕率・限界利益率などを分析します。",
        "gradient": "linear-gradient(135deg, #6f42c1 0%, #9b59b6 100%)",
    },
    "contribution_analysis.html": {
        "icon": "fas fa-layer-group",
        "title": "貢献利益分析",
        "subtitle": "製品・部門別の貢献利益を分析します。",
        "gradient": "linear-gradient(135deg, #6f42c1 0%, #9b59b6 100%)",
    },
    "differential_cost_analysis.html": {
        "icon": "fas fa-balance-scale",
        "title": "差額原価分析",
        "subtitle": "意思決定のための差額原価・差額収益を分析します。",
        "gradient": "linear-gradient(135deg, #6f42c1 0%, #9b59b6 100%)",
    },
    "debt_capacity_analysis.html": {
        "icon": "fas fa-hand-holding-usd",
        "title": "借入余力分析",
        "subtitle": "借入可能額・返済能力を分析します。",
        "gradient": "linear-gradient(135deg, #c0392b 0%, #fd7e14 100%)",
    },
    "capital_investment_planning.html": {
        "icon": "fas fa-industry",
        "title": "設備投資計画",
        "subtitle": "設備投資の採算性・回収期間を分析します。",
        "gradient": "linear-gradient(135deg, #1e7e34 0%, #28a745 100%)",
    },
    "working_capital_planning.html": {
        "icon": "fas fa-sync-alt",
        "title": "運転資金計画",
        "subtitle": "運転資金の必要額・調達計画を管理します。",
        "gradient": "linear-gradient(135deg, #1e7e34 0%, #28a745 100%)",
    },
    "fiscal_year_list.html": {
        "icon": "fas fa-calendar-alt",
        "title": "会計年度管理",
        "subtitle": "会計年度の設定・管理を行います。",
        "gradient": "linear-gradient(135deg, #1e7e34 0%, #28a745 100%)",
    },
    "fiscal_year_form.html": {
        "icon": "fas fa-calendar-plus",
        "gradient": "linear-gradient(135deg, #1e7e34 0%, #28a745 100%)",
    },
}

def remove_duplicate_bootstrap(filepath):
    """個別のBootstrap/FontAwesome読み込みを削除する"""
    with open(filepath, 'r') as f:
        content = f.read()

    # extra_headブロック内のBootstrap/FontAwesome読み込みを削除
    patterns = [
        r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/bootstrap@[^"]+/dist/css/bootstrap\.min\.css">\s*\n',
        r'<link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+/css/all\.min\.css">\s*\n',
        r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/bootstrap-icons@[^"]+/font/bootstrap-icons\.min\.css">\s*\n',
        r'<script src="https://cdn\.jsdelivr\.net/npm/bootstrap@[^"]+/dist/js/bootstrap\.bundle\.min\.js"></script>\s*\n',
    ]

    original = content
    for pattern in patterns:
        content = re.sub(pattern, '', content)

    # extra_headブロックが空になった場合は削除
    content = re.sub(r'\{%\s*block extra_head\s*%\}\s*\{%\s*endblock\s*%\}', '', content)
    content = re.sub(r'\{%\s*block extra_scripts\s*%\}\s*\{%\s*endblock\s*%\}', '', content)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  Cleaned Bootstrap imports: {os.path.basename(filepath)}")
    return content != original

def upgrade_page_header(filepath, config):
    """旧スタイルのヘッダーをグラデーションカードヘッダーに変換する"""
    with open(filepath, 'r') as f:
        content = f.read()

    # 旧スタイルのヘッダーパターンを検出して置換
    # パターン1: <div class="row mb-4"><div class="col-md-8"><h2>...</h2>...</div>...</div>
    pattern1 = r'(<div class="row mb-4">\s*<div class="col-(?:md|12)-?\d*">\s*<h2[^>]*>)(.*?)(</h2>)\s*(<p class="text-muted">)(.*?)(</p>)\s*</div>'

    def replace_header1(m):
        icon = config.get('icon', 'fas fa-chart-line')
        gradient = config.get('gradient', 'linear-gradient(135deg, #0056b3 0%, #007bff 100%)')
        title = m.group(2).strip()
        subtitle = m.group(5).strip()
        # アイコンタグを除去してテキストのみ取得
        title_text = re.sub(r'<[^>]+>', '', title).strip()
        subtitle_text = re.sub(r'<[^>]+>', '', subtitle).strip()
        return f'''<div class="card shadow-sm border-0 mb-4" style="background: {gradient};">
    <div class="card-body text-white py-4">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
        <div>
          <h3 class="mb-1 fw-bold"><i class="{icon} me-2"></i>{title_text}</h3>
          <p class="mb-0 opacity-75">{subtitle_text}</p>
        </div>'''

    new_content, n = re.subn(pattern1, replace_header1, content, flags=re.DOTALL)
    if n > 0:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"  Upgraded header: {os.path.basename(filepath)}")
        return True
    return False

def convert_tailwind_to_bootstrap(filepath):
    """Tailwind CSSクラスをBootstrap5クラスに変換する（基本的なもの）"""
    with open(filepath, 'r') as f:
        content = f.read()

    replacements = [
        # コンテナ
        (r'class="container mx-auto px-4 py-8"', 'class="container-fluid mt-4 px-3 px-md-4"'),
        (r'class="max-w-7xl mx-auto"', 'class=""'),
        # テキスト
        (r'class="text-3xl font-bold mb-6"', 'class="fw-bold mb-3 fs-3"'),
        (r'class="text-xl font-semibold mb-4"', 'class="fw-semibold mb-3 fs-5"'),
        (r'class="text-gray-600 mb-6"', 'class="text-muted mb-4"'),
        (r'class="text-sm font-medium text-gray-700 mb-2"', 'class="form-label fw-medium"'),
        (r'class="block text-sm font-medium text-gray-700 mb-2"', 'class="form-label fw-medium"'),
        # カード
        (r'class="bg-white rounded-lg shadow p-6 mb-6"', 'class="card shadow-sm mb-4 p-4"'),
        (r'class="bg-white rounded-lg shadow p-6"', 'class="card shadow-sm p-4"'),
        # グリッド
        (r'class="grid grid-cols-1 md:grid-cols-3 gap-4"', 'class="row g-3"'),
        (r'class="grid grid-cols-1 md:grid-cols-2 gap-6"', 'class="row g-3"'),
        # セレクト
        (r'class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"', 'class="form-select"'),
        # ボタン
        (r'class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"', 'class="btn btn-primary"'),
        (r'class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"', 'class="btn btn-success"'),
    ]

    original = content
    for old, new in replacements:
        content = content.replace(old, new)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  Converted Tailwind: {os.path.basename(filepath)}")
        return True
    return False

def add_page_header_to_tailwind(filepath, config):
    """Tailwindページにグラデーションヘッダーを追加する"""
    with open(filepath, 'r') as f:
        content = f.read()

    icon = config.get('icon', 'fas fa-chart-line')
    title = config.get('title', '')
    subtitle = config.get('subtitle', '')
    gradient = config.get('gradient', 'linear-gradient(135deg, #0056b3 0%, #007bff 100%)')

    if not title:
        return False

    # h1タグを探してグラデーションヘッダーに置換
    pattern = r'(<h1[^>]*>)(.*?)(</h1>)\s*(<p[^>]*>)(.*?)(</p>)'
    def replace_h1(m):
        return f'''<div class="card shadow-sm border-0 mb-4" style="background: {gradient};">
    <div class="card-body text-white py-4">
      <h3 class="mb-1 fw-bold"><i class="{icon} me-2"></i>{title}</h3>
      <p class="mb-0 opacity-75">{subtitle}</p>
    </div>
  </div>'''

    new_content, n = re.subn(pattern, replace_h1, content, flags=re.DOTALL)
    if n > 0:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"  Added gradient header: {os.path.basename(filepath)}")
        return True
    return False

# Tailwindページの設定
TAILWIND_PAGES = {
    "dashboard_analysis.html": {
        "icon": "fas fa-tachometer-alt",
        "title": "ダッシュボード分析",
        "subtitle": "企業と会計年度を選択して財務分析を実行します。",
        "gradient": "linear-gradient(135deg, #c0392b 0%, #fd7e14 100%)",
    },
    "simulation.html": {
        "icon": "fas fa-calculator",
        "title": "経営シミュレーション",
        "subtitle": "過去の実績データをベースに、将来の財務状況をシミュレーションします。",
        "gradient": "linear-gradient(135deg, #6f42c1 0%, #9b59b6 100%)",
    },
}

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=== Bootstrap重複読み込みを削除 ===")
    for fname in REMOVE_BOOTSTRAP_FILES:
        fpath = os.path.join(TEMPLATES_DIR, fname)
        if os.path.exists(fpath):
            remove_duplicate_bootstrap(fpath)

    print("\n=== ヘッダーをグラデーションカードに変換 ===")
    for fname, config in HEADER_UPGRADES.items():
        fpath = os.path.join(TEMPLATES_DIR, fname)
        if os.path.exists(fpath):
            upgrade_page_header(fpath, config)

    print("\n=== TailwindページにBootstrapヘッダーを追加 ===")
    for fname, config in TAILWIND_PAGES.items():
        fpath = os.path.join(TEMPLATES_DIR, fname)
        if os.path.exists(fpath):
            convert_tailwind_to_bootstrap(fpath)
            add_page_header_to_tailwind(fpath, config)

    print("\n完了!")
