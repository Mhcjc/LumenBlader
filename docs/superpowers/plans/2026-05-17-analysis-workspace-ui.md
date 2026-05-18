# Analysis Workspace UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the analysis workspace page with tabbed report viewer, improved card styling, skeleton loading, and smooth animations.

**Architecture:** Enhance existing vanilla JS SPA. Add Open Props + Fira Code via CDN. Rewrite `analysis.js` for expandable cards and tab logic. Add new CSS tokens and component styles to `style.css`.

**Tech Stack:** Vanilla JS, CSS custom properties, Open Props (CDN), marked.js (existing), Fira Code + Inter (Google Fonts)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `frontend/index.html` | Add CDN links (Open Props, Fira Code) |
| `frontend/css/style.css` | New design tokens, card-status styles, tab styles, skeleton-card styles, markdown report styles, stagger animation |
| `frontend/js/analysis.js` | Full rewrite: expandable cards, tab rendering, markdown splitting, search filter, skeleton loading |

---

### Task 1: Add CDN Links to index.html

**Files:**
- Modify: `frontend/index.html:1-8`

- [ ] **Step 1: Add Open Props and Fira Code CDN links**

In `frontend/index.html`, add two lines in the `<head>` after the existing `<link>` tag (line 7):

```html
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/open-props@1.7.4/open-props.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

Remove the old Inter-only font import from `style.css` line 1 (the new link above replaces it).

- [ ] **Step 2: Verify fonts load**

Open `http://localhost:8080` in browser. Check DevTools → Network tab: `open-props.min.css`, `Fira Code` font files should load with 200 status.

- [ ] **Step 3: Commit**

```bash
git add frontend/index.html frontend/css/style.css
git commit -m "feat: add Open Props and Fira Code CDN links"
```

---

### Task 2: Add New Design Tokens to style.css

**Files:**
- Modify: `frontend/css/style.css:1-30`

- [ ] **Step 1: Replace font import and add new tokens**

Replace line 1 of `style.css`:

```css
/* Font import moved to index.html CDN links */
```

Add new tokens to the `:root` block (after existing tokens, before the closing `}`):

```css
    /* New tokens for analysis workspace */
    --bg-elevated: #273548;
    --bg-deep: #0B1120;
    --accent-secondary: #3B82F6;
    --accent-secondary-muted: rgba(59, 130, 246, 0.12);
    --text-primary: #F1F5F9;
    --border-subtle-hairline: rgba(255, 255, 255, 0.08);
    --font-mono: 'Fira Code', 'SF Mono', 'Cascadia Code', monospace;
```

- [ ] **Step 2: Verify no visual regression**

Open `http://localhost:8080`. All three pages should look identical to before (new tokens are additive, not replacing existing ones).

- [ ] **Step 3: Commit**

```bash
git add frontend/css/style.css
git commit -m "feat: add new design tokens for analysis workspace"
```

---

### Task 3: Add Card Status Styles to style.css

**Files:**
- Modify: `frontend/css/style.css` (add after the `.card-clickable:hover` block, around line 133)

- [ ] **Step 1: Add video card status styles**

Add after the `.card-clickable:hover` block:

```css
/* ─── Video Card Status ─── */
.video-card {
    position: relative;
    padding-left: 16px;
    border-left: 3px solid transparent;
    transition: border-color var(--transition), background var(--transition), transform var(--transition), box-shadow var(--transition);
}

.video-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.video-card[data-status="analyzed"] { border-left-color: var(--accent); }
.video-card[data-status="processing"] { border-left-color: var(--accent-secondary); }
.video-card[data-status="pending"] { border-left-color: var(--warning); }
.video-card[data-status="unanalyzed"] { border-left-color: var(--text-dim); }

.video-card.expanded {
    border-color: var(--accent);
    background: var(--bg-elevated);
}

.video-card.dimmed {
    opacity: 0.6;
    pointer-events: none;
}
```

- [ ] **Step 2: Verify existing cards unaffected**

The `.video-card` class is new — existing `.card` elements are unaffected. No visual change yet.

- [ ] **Step 3: Commit**

```bash
git add frontend/css/style.css
git commit -m "feat: add video card status border styles"
```

---

### Task 4: Add Tab and Report Styles to style.css

**Files:**
- Modify: `frontend/css/style.css` (add after the skeleton section, before the empty-state section)

- [ ] **Step 1: Add tab bar styles**

```css
/* ─── Report Tabs ─── */
.report-tabs {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
}

.report-tabs::-webkit-scrollbar { display: none; }

.report-tab {
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-dim);
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    white-space: nowrap;
    transition: color var(--transition), border-color var(--transition);
}

.report-tab:hover { color: var(--text-secondary); }

.report-tab.active {
    color: var(--text-primary);
    border-bottom-color: var(--accent);
}

.report-content {
    padding: 20px;
    animation: tab-fade 0.15s ease;
}

@keyframes tab-fade {
    from { opacity: 0; }
    to { opacity: 1; }
}
```

- [ ] **Step 2: Add expanded report area styles**

```css
/* ─── Expanded Report ─── */
.report-expanded {
    background: var(--bg-deep);
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    margin-top: -8px;
    margin-bottom: 16px;
    overflow: hidden;
    animation: report-expand 0.3s ease-out;
}

@keyframes report-expand {
    from { opacity: 0; max-height: 0; }
    to { opacity: 1; max-height: 2000px; }
}

.report-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-card);
}

.report-header-filename {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--text-primary);
}

.report-close {
    background: none;
    border: none;
    color: var(--text-dim);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 18px;
    line-height: 1;
    transition: color var(--transition), background var(--transition);
}

.report-close:hover {
    color: var(--text);
    background: var(--bg-input);
}
```

- [ ] **Step 3: Verify no conflicts**

Open `http://localhost:8080` — no visual change (new classes not yet used in HTML).

- [ ] **Step 4: Commit**

```bash
git add frontend/css/style.css
git commit -m "feat: add tab bar and expanded report styles"
```

---

### Task 5: Add Markdown Report Rendering Styles to style.css

**Files:**
- Modify: `frontend/css/style.css` (add after the report styles from Task 4)

- [ ] **Step 1: Add markdown content styles**

```css
/* ─── Markdown Report Content ─── */
.report-content h1 {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 12px;
    color: var(--text-primary);
}

.report-content h2 {
    font-size: 17px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 10px;
    padding-left: 12px;
    border-left: 3px solid var(--accent);
    color: var(--text-primary);
}

.report-content h3 {
    font-size: 15px;
    font-weight: 600;
    margin-top: 16px;
    margin-bottom: 8px;
    color: var(--text-secondary);
}

.report-content p {
    margin-bottom: 10px;
    line-height: 1.7;
}

.report-content ul, .report-content ol {
    margin-bottom: 12px;
    padding-left: 24px;
}

.report-content li {
    margin-bottom: 4px;
    line-height: 1.6;
}

.report-content ul li::marker {
    color: var(--accent);
}

.report-content ol li {
    font-family: var(--font-mono);
    font-size: 13px;
}

.report-content strong {
    color: var(--text-primary);
}

.report-content blockquote {
    border-left: 3px solid var(--accent-secondary);
    padding: 8px 16px;
    margin: 12px 0;
    background: rgba(59, 130, 246, 0.06);
    border-radius: 0 var(--radius) var(--radius) 0;
    color: var(--text-secondary);
}

.report-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 13px;
}

.report-content th, .report-content td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

.report-content th {
    font-weight: 600;
    color: var(--text-primary);
    background: var(--bg-elevated);
}

.report-content tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
}
```

- [ ] **Step 2: Verify styles don't leak**

These styles are scoped to `.report-content` — they won't affect other pages.

- [ ] **Step 3: Commit**

```bash
git add frontend/css/style.css
git commit -m "feat: add markdown report rendering styles"
```

---

### Task 6: Add Skeleton Card and Stagger Animation to style.css

**Files:**
- Modify: `frontend/css/style.css` (add before the responsive section)

- [ ] **Step 1: Add skeleton card styles**

```css
/* ─── Skeleton Cards ─── */
.skeleton-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    padding-left: 19px;
}

.skeleton-line {
    height: 12px;
    border-radius: 4px;
    margin-bottom: 8px;
}

.skeleton-line:last-child {
    width: 60%;
    margin-bottom: 0;
}

/* ─── Stagger Animation ─── */
.stagger-in {
    animation: stagger-fade-in 0.3s ease-out both;
}

@keyframes stagger-fade-in {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ─── Account Search ─── */
.account-search {
    margin-bottom: 12px;
}

.account-search input {
    font-size: 13px;
    padding: 8px 12px;
}

.account-item {
    transition: border-color var(--transition), background var(--transition);
}

.account-item.selected {
    border-left: 3px solid var(--accent);
    background: var(--bg-elevated);
}
```

- [ ] **Step 2: Verify no visual regression**

New classes not yet used — no change visible.

- [ ] **Step 3: Commit**

```bash
git add frontend/css/style.css
git commit -m "feat: add skeleton card and stagger animation styles"
```

---

### Task 7: Rewrite analysis.js — Skeleton and Search

**Files:**
- Modify: `frontend/js/analysis.js` (full rewrite)

- [ ] **Step 1: Replace the loadAnalysis function**

Replace the entire `loadAnalysis` function (lines 3-41) with:

```javascript
let currentFolder = null;
let expandedStem = null;

async function loadAnalysis() {
    const container = document.getElementById('page-analysis');
    container.innerHTML = `
        <h1 style="margin-bottom: 20px; font-size: 20px; font-weight: 600;">分析工作台</h1>
        <div class="flex gap-16" style="align-items: flex-start;">
            <div style="width: 260px; flex-shrink: 0;">
                <div class="section-header">选择博主</div>
                <div class="account-search">
                    <input type="text" id="account-filter" placeholder="搜索博主..." oninput="filterAccounts()">
                </div>
                <div id="analysis-accounts"></div>
            </div>
            <div style="flex: 1; min-width: 0;">
                <div id="analysis-content">
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128270;</div>
                        <p class="empty-state-text">请先从左侧选择一个博主</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    try {
        const accounts = await API.get('/api/accounts');
        const list = document.getElementById('analysis-accounts');

        if (accounts.length === 0) {
            list.innerHTML = '<div class="empty-state" style="padding: 24px 16px;"><p class="empty-state-text">暂无博主</p></div>';
            return;
        }

        list.innerHTML = accounts.map((acc, i) => `
            <div class="card card-clickable account-item stagger-in" style="padding: 12px; margin-bottom: 8px; animation-delay: ${i * 50}ms;" onclick="loadAccountAnalysis('${acc.folder_name}', this)" data-nickname="${acc.nickname.toLowerCase()}">
                <span class="badge badge-${acc.platform}">${acc.platform === 'douyin' ? '抖音' : 'TikTok'}</span>
                <span style="margin-left: 8px; font-weight: 500;">${acc.nickname}</span>
            </div>
        `).join('');

        window._allAccounts = accounts;
    } catch (e) {
        console.error('Failed to load accounts:', e);
    }
}

function filterAccounts() {
    const query = document.getElementById('account-filter').value.toLowerCase();
    const items = document.querySelectorAll('#analysis-accounts .account-item');
    items.forEach(item => {
        const nickname = item.dataset.nickname || '';
        item.style.display = nickname.includes(query) ? '' : 'none';
    });
}
```

- [ ] **Step 2: Verify account list loads**

Open `http://localhost:8080`, navigate to 分析工作台. Accounts should appear with staggered fade-in animation. Search input visible.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/analysis.js
git commit -m "feat: add account search and stagger animation to analysis page"
```

---

### Task 8: Rewrite analysis.js — Video List with Skeleton Loading

**Files:**
- Modify: `frontend/js/analysis.js`

- [ ] **Step 1: Replace loadAccountAnalysis function**

Replace the entire `loadAccountAnalysis` function (lines 43-106) with:

```javascript
async function loadAccountAnalysis(folderName, el) {
    currentFolder = folderName;
    expandedStem = null;

    // Highlight selected account
    document.querySelectorAll('.account-item').forEach(a => a.classList.remove('selected'));
    if (el) el.classList.add('selected');

    const content = document.getElementById('analysis-content');

    // Show skeleton loading
    content.innerHTML = `
        <div class="flex flex-between" style="margin-bottom: 16px;">
            <h2 style="font-size: 18px; font-weight: 600;">${folderName}</h2>
            <div class="flex gap-8">
                <select id="analysis-mode" style="width: auto;">
                    <option value="summary">摘要模式</option>
                    <option value="full">Full 分析</option>
                </select>
                <button class="btn btn-primary" onclick="batchAnalyze()">批量分析</button>
            </div>
        </div>
        <div class="grid grid-3" id="video-list">
            ${Array(6).fill(0).map(() => `
                <div class="skeleton-card">
                    <div class="skeleton skeleton-line" style="width: 80%;"></div>
                    <div class="skeleton skeleton-line" style="width: 40%;"></div>
                </div>
            `).join('')}
        </div>
    `;

    try {
        const data = await API.get(`/api/files/${folderName}`);
        const videos = data.videos || [];
        const analysis = data.analysis || [];
        const analysisJobs = data.analysis_jobs || {};
        const analyzedSet = new Set(analysis.map(a => a.name.replace('.md', '')));

        if (videos.length === 0) {
            content.innerHTML = `
                <div class="flex flex-between" style="margin-bottom: 16px;">
                    <h2 style="font-size: 18px; font-weight: 600;">${folderName}</h2>
                </div>
                <div class="empty-state">
                    <div class="empty-state-icon">&#127916;</div>
                    <p class="empty-state-text">暂无视频文件<br>请先在下载中心下载视频</p>
                </div>
            `;
            return;
        }

        const videoListHtml = videos.map((v, i) => {
            const stem = v.name.replace('.mp4', '');
            const hasAnalysis = analyzedSet.has(stem);
            const jobStatus = analysisJobs[stem];
            let status = 'unanalyzed';
            let badge = '<span class="badge badge-warning">未分析</span>';
            if (hasAnalysis) {
                status = 'analyzed';
                badge = '<span class="badge badge-success">已分析</span>';
            } else if (jobStatus === 'processing') {
                status = 'processing';
                badge = '<span class="badge badge-info">分析中</span>';
            } else if (jobStatus === 'pending') {
                status = 'pending';
                badge = '<span class="badge badge-warning">等待中</span>';
            }
            return `
                <div class="card card-clickable video-card stagger-in"
                     data-status="${status}"
                     data-stem="${stem}"
                     style="animation-delay: ${i * 50}ms;"
                     onclick="toggleReport('${folderName}', '${stem}', this)">
                    <div class="flex flex-between">
                        <span style="font-weight: 500; font-size: 13px; font-family: var(--font-mono);">${v.name}</span>
                        ${badge}
                    </div>
                    <p style="font-size: 12px; color: var(--text-dim); margin-top: 6px;">
                        ${(v.size / 1024 / 1024).toFixed(1)} MB
                    </p>
                </div>
            `;
        }).join('');

        content.innerHTML = `
            <div class="flex flex-between" style="margin-bottom: 16px;">
                <h2 style="font-size: 18px; font-weight: 600;">${folderName}</h2>
                <div class="flex gap-8">
                    <select id="analysis-mode" style="width: auto;">
                        <option value="summary">摘要模式</option>
                        <option value="full">Full 分析</option>
                    </select>
                    <button class="btn btn-primary" onclick="batchAnalyze()">批量分析</button>
                </div>
            </div>
            <div class="grid grid-3" id="video-list">
                ${videoListHtml}
            </div>
            <div id="report-container"></div>
        `;
    } catch (e) {
        content.innerHTML = `<div class="empty-state"><p style="color: var(--danger);">加载失败: ${e.message}</p></div>`;
    }
}
```

- [ ] **Step 2: Verify skeleton loading and card styling**

Navigate to 分析工作台, click an account. Should see skeleton cards briefly, then real video cards with colored left borders and staggered entrance.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/analysis.js
git commit -m "feat: skeleton loading and styled video cards"
```

---

### Task 9: Rewrite analysis.js — Expandable Report with Tabs

**Files:**
- Modify: `frontend/js/analysis.js`

- [ ] **Step 1: Add toggleReport and tab rendering functions**

Add these functions after `loadAccountAnalysis`:

```javascript
async function toggleReport(folderName, stem, cardEl) {
    const container = document.getElementById('report-container');

    // If clicking the already-expanded card, collapse it
    if (expandedStem === stem) {
        collapseReport();
        return;
    }

    // Collapse any existing report
    expandedStem = stem;

    // Dim other cards
    document.querySelectorAll('.video-card').forEach(c => {
        c.classList.remove('expanded', 'dimmed');
        if (c.dataset.stem !== stem) c.classList.add('dimmed');
        else c.classList.add('expanded');
    });

    // Show report container with skeleton
    container.innerHTML = `
        <div class="report-expanded">
            <div class="report-header">
                <span class="report-header-filename">${stem}.mp4</span>
                <button class="report-close" onclick="collapseReport()">&times;</button>
            </div>
            <div class="report-content" style="padding: 20px;">
                <div class="skeleton skeleton-line" style="width: 90%;"></div>
                <div class="skeleton skeleton-line" style="width: 75%;"></div>
                <div class="skeleton skeleton-line" style="width: 60%;"></div>
            </div>
        </div>
    `;

    try {
        const data = await API.get(`/api/files/${folderName}/analysis/${stem}.md`);
        const mode = document.getElementById('analysis-mode')?.value || 'summary';
        renderReport(data.content, stem, mode);
    } catch (e) {
        container.innerHTML = `
            <div class="report-expanded">
                <div class="report-header">
                    <span class="report-header-filename">${stem}.mp4</span>
                    <button class="report-close" onclick="collapseReport()">&times;</button>
                </div>
                <div style="padding: 24px; text-align: center;">
                    <p style="color: var(--text-dim); margin-bottom: 12px;">暂无分析报告</p>
                    <button class="btn btn-primary" onclick="analyzeOne('${folderName}', '${stem}')">生成分析</button>
                </div>
            </div>
        `;
    }
}

function collapseReport() {
    expandedStem = null;
    document.querySelectorAll('.video-card').forEach(c => c.classList.remove('expanded', 'dimmed'));
    document.getElementById('report-container').innerHTML = '';
}

function renderReport(markdown, stem, mode) {
    const sections = splitMarkdownSections(markdown);
    const container = document.getElementById('report-container');

    let tabs;
    if (mode === 'full') {
        tabs = [
            { label: '摘要', sections: [0, 1] },
            { label: '评分', sections: [2, 3] },
            { label: '预测', sections: [4] },
            { label: '建议', sections: [5, 6] },
        ];
    } else {
        tabs = [
            { label: '摘要', sections: [0, 1] },
            { label: '亮点', sections: [2, 3] },
        ];
    }

    const tabButtons = tabs.map((t, i) =>
        `<button class="report-tab ${i === 0 ? 'active' : ''}" onclick="switchTab(${i}, this)">${t.label}</button>`
    ).join('');

    const tabContents = tabs.map((t, i) => {
        const content = t.sections
            .filter(idx => idx < sections.length)
            .map(idx => sections[idx])
            .join('\n\n');
        return `<div class="report-content tab-panel" style="display: ${i === 0 ? 'block' : 'none'};">${marked(content)}</div>`;
    }).join('');

    container.innerHTML = `
        <div class="report-expanded">
            <div class="report-header">
                <span class="report-header-filename">${stem}.mp4</span>
                <button class="report-close" onclick="collapseReport()">&times;</button>
            </div>
            <div class="report-tabs">${tabButtons}</div>
            ${tabContents}
        </div>
    `;
}

function switchTab(index, btn) {
    document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach((p, i) => {
        p.style.display = i === index ? 'block' : 'none';
        if (i === index) {
            p.style.animation = 'none';
            p.offsetHeight; // trigger reflow
            p.style.animation = 'tab-fade 0.15s ease';
        }
    });
}

function splitMarkdownSections(markdown) {
    // Split by numbered section headers: ## 1. or **1.**
    const lines = markdown.split('\n');
    const sections = [];
    let current = [];

    for (const line of lines) {
        const isNewSection = /^#{1,3}\s+\d+\./.test(line) || /^\*\*\d+\./.test(line);
        if (isNewSection && current.length > 0) {
            sections.push(current.join('\n'));
            current = [];
        }
        current.push(line);
    }
    if (current.length > 0) {
        sections.push(current.join('\n'));
    }

    // If parsing produced fewer than 2 sections, return full content as single section
    if (sections.length < 2) {
        return [markdown];
    }

    return sections;
}
```

- [ ] **Step 2: Verify expand/collapse behavior**

Click a video card — report should expand below with skeleton, then show tabbed content. Click another card — previous collapses, new one expands. Click X — collapses.

- [ ] **Step 3: Verify tab switching**

In expanded report, click each tab. Content should crossfade. Active tab has green underline.

- [ ] **Step 4: Commit**

```bash
git add frontend/js/analysis.js
git commit -m "feat: expandable report with tabbed sections"
```

---

### Task 10: Rewrite analysis.js — Batch Analyze and Button Loading

**Files:**
- Modify: `frontend/js/analysis.js`

- [ ] **Step 1: Replace analyzeOne and batchAnalyze with loading states**

Replace both functions:

```javascript
async function analyzeOne(folderName, stem) {
    const mode = document.getElementById('analysis-mode')?.value || 'summary';
    try {
        await API.post('/api/analysis/start', {
            video_path: `../materials/${folderName}/videos/${stem}.mp4`,
            mode,
        });
        showToast('分析任务已创建，请稍后刷新查看结果', 'success');
        loadAccountAnalysis(folderName);
    } catch (e) {
        showToast('分析失败: ' + e.message, 'error');
    }
}

async function batchAnalyze() {
    if (!currentFolder) return;
    const mode = document.getElementById('analysis-mode')?.value || 'summary';
    const btn = event.target;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner spinner-sm"></span> 分析中...';

    try {
        const accounts = await API.get('/api/accounts');
        const account = accounts.find(a => a.folder_name === currentFolder);
        if (!account) {
            showToast('未找到对应博主', 'error');
            return;
        }

        const result = await API.post('/api/analysis/batch', {
            account_id: account.id,
            mode,
        });
        showToast(`已创建 ${result.created} 个分析任务`, 'success');
        loadAccountAnalysis(currentFolder);
    } catch (e) {
        showToast('批量分析失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '批量分析';
    }
}
```

- [ ] **Step 2: Verify button loading state**

Click 批量分析 — button should show spinner + "分析中..." text, then revert after completion.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/analysis.js
git commit -m "feat: button loading states for analysis actions"
```

---

### Task 11: Final Verification and Grid Spacing Fix

**Files:**
- Modify: `frontend/css/style.css` (minor grid gap update)

- [ ] **Step 1: Update grid gap**

In `style.css`, change the `.grid` rule (line 311):

From: `.grid { display: grid; gap: 16px; }`
To: `.grid { display: grid; gap: 20px; }`

- [ ] **Step 2: Full integration test**

1. Open `http://localhost:8080`
2. Navigate to 分析工作台
3. Verify: accounts load with stagger animation, search filter works
4. Click an account: skeleton loading → video cards with colored left borders
5. Click a video card: expandable report with tabs
6. Switch tabs: crossfade animation
7. Click another card: previous collapses, new expands
8. Click 批量分析: button shows loading state
9. Resize to mobile: grid collapses to 1 column, tabs scroll horizontally
10. Check `prefers-reduced-motion`: animations disabled

- [ ] **Step 3: Final commit**

```bash
git add frontend/css/style.css frontend/js/analysis.js frontend/index.html
git commit -m "feat: complete analysis workspace UI overhaul"
```
