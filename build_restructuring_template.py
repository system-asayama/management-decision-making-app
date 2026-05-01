"""
PL組換えとBS組換えを統合した財務諸表組換えテンプレートを生成するスクリプト
- PLとBSのフォーム内容を抽出してタブ統合
- 共通関数（parseNum, fmt, updateSummary, setVal, initCommaInputs）は1つだけ定義
- BSのrecalculateをrecalculateBSにリネーム
- autoFillFromPdfは共通版のみ使用
"""

COMMON_FUNC_NAMES = [
    'function parseNum(',
    'function fmt(',
    'function updateSummary(',
    'function setVal(',
    'function initCommaInputs(',
]

def extract_form(lines, start_0idx, end_0idx):
    return ''.join(lines[start_0idx:end_0idx])

def extract_script_without_common_and_autofill(lines, script_start_0idx, script_end_0idx, rename_recalculate=False):
    """スクリプト行から共通関数とautoFillFromPdfを除去する"""
    raw = lines[script_start_0idx:script_end_0idx]
    result = []
    skip = False
    brace_depth = 0
    i = 0
    while i < len(raw):
        line = raw[i]
        stripped = line.strip()
        # 共通関数またはautoFillFromPdfの開始を検出
        is_common = any(fn in line for fn in COMMON_FUNC_NAMES)
        is_autofill = 'function autoFillFromPdf(' in line
        is_autofill_comment = '// 財務諸表から自動読み取り' in line
        if is_common or is_autofill or is_autofill_comment:
            skip = True
            brace_depth = 0
        if skip:
            brace_depth += line.count('{') - line.count('}')
            if brace_depth <= 0 and ('{' in line or '}' in line):
                skip = False
            i += 1
            continue
        # BSのrecalculate → recalculateBS にリネーム
        if rename_recalculate:
            line = line.replace('function recalculate()', 'function recalculateBS()')
            line = line.replace('recalculate();', 'recalculateBS();')
        result.append(line)
        i += 1
    return ''.join(result)

def find_script_range(lines):
    start = None
    for i, l in enumerate(lines):
        if '<script>' in l and i > 500:
            start = i + 1
            break
    end = None
    for i in range(start, len(lines)):
        if '</script>' in lines[i]:
            end = i
            break
    return start, end

with open('app/templates/pl_restructuring.html', 'r', encoding='utf-8') as f:
    pl_lines = f.readlines()

with open('app/templates/bs_restructuring.html', 'r', encoding='utf-8') as f:
    bs_lines = f.readlines()

# フォーム内容
pl_form_content = extract_form(pl_lines, 54, 517)
bs_form_content = extract_form(bs_lines, 54, 548)

# スクリプト内容
pl_script_start, pl_script_end = find_script_range(pl_lines)
bs_script_start, bs_script_end = find_script_range(bs_lines)

pl_script = extract_script_without_common_and_autofill(pl_lines, pl_script_start, pl_script_end, rename_recalculate=False)
bs_script = extract_script_without_common_and_autofill(bs_lines, bs_script_start, bs_script_end, rename_recalculate=True)

print(f"PL script lines: {len(pl_script.splitlines())}")
print(f"BS script lines: {len(bs_script.splitlines())}")

template = '''{% extends "base.html" %}
{% block title %}財務諸表組換え{% endblock %}
{% block content %}
<div class="container mt-4">
    <div class="row mb-3">
        <div class="col-12">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="/decision/">経営意思決定アプリ</a></li>
                    <li class="breadcrumb-item active">財務諸表組換え</li>
                </ol>
            </nav>
            <h2><i class="fas fa-exchange-alt me-2 text-primary"></i>財務諸表の組換え</h2>
            <p class="text-muted">損益計算書・貸借対照表を経営分析用に組換えます。</p>
        </div>
    </div>

    <!-- 会計年度選択 -->
    <div class="card mb-4">
        <div class="card-header bg-primary text-white">
            <i class="fas fa-calendar-alt me-2"></i>会計年度・企業の選択
        </div>
        <div class="card-body">
            <form method="GET" action="/decision/restructuring" class="row g-3">
                <div class="col-md-4">
                    <label class="form-label">企業</label>
                    <select name="company_id" class="form-select" onchange="this.form.submit()">
                        <option value="">企業を選択</option>
                        {% for c in companies %}
                        <option value="{{ c.id }}" {% if selected_company and selected_company.id == c.id %}selected{% endif %}>{{ c.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">会計年度</label>
                    <select name="fiscal_year_id" class="form-select" onchange="this.form.submit()">
                        <option value="">会計年度を選択</option>
                        {% for fy in fiscal_years %}
                        <option value="{{ fy.id }}" {% if selected_fy and selected_fy.id == fy.id %}selected{% endif %}>{{ fy.year_name }}</option>
                        {% endfor %}
                    </select>
                </div>
            </form>
        </div>
    </div>

    {% if selected_fy %}
    <!-- 自動読み取りボタン -->
    <div class="d-flex justify-content-end mb-3">
        <button type="button" id="btnAutoFill" class="btn btn-warning fw-bold" onclick="autoFillFromPdf()">
            <i class="fas fa-magic me-1"></i>財務諸表から自動読み取り
        </button>
    </div>
    <div id="autoFillAlert" class="alert d-none mb-3" role="alert"></div>

    <!-- PL/BSタブ -->
    <ul class="nav nav-tabs mb-0" id="restructuringTabs" role="tablist">
        <li class="nav-item" role="presentation">
            <button class="nav-link {% if active_tab != 'bs' %}active{% endif %}" id="pl-tab" data-bs-toggle="tab" data-bs-target="#pl-pane" type="button" role="tab" onclick="clearAutoFillAlert()">
                <i class="fas fa-chart-line me-1"></i>損益計算書（PL）
            </button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link {% if active_tab == 'bs' %}active{% endif %}" id="bs-tab" data-bs-toggle="tab" data-bs-target="#bs-pane" type="button" role="tab" onclick="clearAutoFillAlert()">
                <i class="fas fa-balance-scale me-1"></i>貸借対照表（BS）
            </button>
        </li>
    </ul>
    <div class="tab-content border border-top-0 rounded-bottom bg-white p-3 mb-4" id="restructuringTabContent">

        <!-- PLタブ -->
        <div class="tab-pane fade {% if active_tab != 'bs' %}show active{% endif %}" id="pl-pane" role="tabpanel">
''' + pl_form_content + '''
        </div><!-- /PLタブ -->

        <!-- BSタブ -->
        <div class="tab-pane fade {% if active_tab == 'bs' %}show active{% endif %}" id="bs-pane" role="tabpanel">
''' + bs_form_content + '''
        </div><!-- /BSタブ -->

    </div><!-- /tab-content -->

    {% else %}
    <div class="alert alert-info">
        <i class="fas fa-info-circle me-2"></i>企業と会計年度を選択してください。
    </div>
    {% endif %}
</div>
<script>
// ===== 共通ユーティリティ =====
function parseNum(id) {
    const el = document.getElementById(id);
    if (!el) return 0;
    return parseInt((el.value || '0').replace(/,/g, '').replace(/[^-\\d]/g, '')) || 0;
}
function fmt(n) {
    if (isNaN(n)) return '0';
    return Math.round(n).toLocaleString('ja-JP');
}
function updateSummary(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = fmt(val);
}
function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = fmt(val);
}
function clearAutoFillAlert() {
    const alertEl = document.getElementById('autoFillAlert');
    if (alertEl) alertEl.className = 'alert d-none mb-3';
}
function initCommaInputs() {
    document.querySelectorAll('.js-comma-int').forEach(function(el) {
        if (!el.readOnly) {
            el.addEventListener('input', function() {
                const raw = this.value.replace(/,/g, '').replace(/[^-\\d]/g, '');
                if (raw !== '') {
                    const num = parseInt(raw);
                    if (!isNaN(num)) {
                        this.value = num.toLocaleString('ja-JP');
                    }
                }
                recalculate();
                recalculateBS();
            });
        }
    });
}

// ===== PL用計算 =====
''' + pl_script + '''
// ===== BS用計算 =====
''' + bs_script + '''
// ===== 自動読み取り（PL/BS共通） =====
function autoFillFromPdf() {
    {% if selected_fy %}
    const fiscalYearId = {{ selected_fy.id }};
    {% endif %}
    const btn = document.getElementById('btnAutoFill');
    const alertEl = document.getElementById('autoFillAlert');
    const activeTabBtn = document.querySelector('#restructuringTabs .nav-link.active');
    const isBs = activeTabBtn && activeTabBtn.id === 'bs-tab';
    const endpoint = isBs ? '/decision/bs-auto-fill' : '/decision/pl-auto-fill';

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>読み取り中...';
    alertEl.className = 'alert d-none mb-3';

    fetch(endpoint + '?fiscal_year_id=' + fiscalYearId)
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.error) {
                alertEl.className = 'alert alert-danger mb-3';
                alertEl.textContent = 'エラー: ' + data.error;
                return;
            }
            let filled = 0;
            Object.keys(data).forEach(function(field) {
                const el = document.getElementById(field);
                if (el && !el.readOnly) {
                    const val = parseInt(data[field]) || 0;
                    el.value = val.toLocaleString('ja-JP');
                    filled++;
                }
            });
            if (isBs) { recalculateBS(); } else { recalculate(); }
            if (filled > 0) {
                alertEl.className = 'alert alert-success mb-3';
                alertEl.innerHTML = '<i class="fas fa-check-circle me-1"></i>' + filled + '項目を自動入力しました。内容を確認して「保存」してください。';
            } else {
                alertEl.className = 'alert alert-warning mb-3';
                alertEl.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>読み取れる科目がありませんでした。勘定科目マスタで組換え先を設定してください。';
            }
        })
        .catch(function(err) {
            alertEl.className = 'alert alert-danger mb-3';
            alertEl.textContent = '通信エラーが発生しました: ' + err;
        })
        .finally(function() {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-magic me-1"></i>財務諸表から自動読み取り';
        });
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    initCommaInputs();
    recalculate();
    recalculateBS();
});
</script>
{% endblock %}
'''

with open('app/templates/restructuring.html', 'w', encoding='utf-8') as f:
    f.write(template)

print(f"統合テンプレート生成完了: app/templates/restructuring.html ({len(template.splitlines())}行)")
