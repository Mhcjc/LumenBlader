let currentFolder = null;
let expandedStem = null;
let analysisPollingTimer = null;

async function loadAnalysis() {
    const container = document.getElementById('page-analysis');
    container.innerHTML = `
        <div class="analysis-layout">
            <aside class="analysis-sidebar">
                <div class="sidebar-header">选择博主</div>
                <div class="sidebar-search">
                    <input type="text" class="input input-sm" id="account-filter" placeholder="搜索博主…" oninput="filterAccounts()">
                </div>
                <div class="sidebar-list" id="analysis-accounts"></div>
            </aside>
            <div class="analysis-main">
                <div id="analysis-content">
                    <div class="empty-state" style="padding-top:120px">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                        <div class="empty-state-title">选择一个博主</div>
                        <div class="empty-state-text">从左侧列表选择博主查看视频和分析报告</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    try {
        const accounts = await API.get('/api/accounts');
        const list = document.getElementById('analysis-accounts');

        if (accounts.length === 0) {
            list.innerHTML = '<div style="padding:16px;font-size:13px;color:var(--gray-400);text-align:center">暂无博主</div>';
            return;
        }

        list.innerHTML = accounts.map(a => `
            <div class="sidebar-item" onclick="loadAccountAnalysis('${a.folder_name}', this)" data-nickname="${a.nickname.toLowerCase()}">
                <span class="badge badge-${a.platform}" style="font-size:9px;padding:1px 5px">${a.platform === 'douyin' ? '抖音' : 'TK'}</span>
                <span class="sidebar-item-name">${a.nickname}</span>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load accounts:', e);
    }
}

function filterAccounts() {
    const query = document.getElementById('account-filter').value.toLowerCase();
    const items = document.querySelectorAll('#analysis-accounts .sidebar-item');
    items.forEach(item => {
        const name = item.querySelector('.sidebar-item-name').textContent.toLowerCase();
        item.style.display = name.includes(query) ? '' : 'none';
    });
}

async function loadAccountAnalysis(folderName, el) {
    currentFolder = folderName;
    expandedStem = null;
    stopAnalysisPolling();

    document.querySelectorAll('.sidebar-item').forEach(a => a.classList.remove('active'));
    if (el) el.classList.add('active');

    const content = document.getElementById('analysis-content');

    content.innerHTML = `
        <div class="analysis-toolbar">
            <div class="analysis-toolbar-left">
                <span class="analysis-folder">${folderName}</span>
            </div>
            <div class="analysis-toolbar-right">
                <select class="input" id="analysis-mode" style="width:auto;padding:6px 32px 6px 12px;font-size:13px">
                    <option value="summary">摘要模式</option>
                    <option value="full">Full 分析</option>
                </select>
                <button class="btn btn-primary btn-sm" onclick="batchAnalyze()">批量分析</button>
            </div>
        </div>
        <div class="video-grid" id="video-list">
            ${Array(6).fill(0).map(() => `
                <div class="card skeleton" style="height:80px"></div>
            `).join('')}
        </div>
        <div id="report-container"></div>
    `;

    try {
        const data = await API.get(`/api/files/${folderName}`);
        const videos = data.videos || [];
        const analysis = data.analysis || [];
        const analysisJobs = data.analysis_jobs || {};
        const analyzedSet = new Set(analysis.map(a => a.name.replace('.md', '')));

        if (videos.length === 0) {
            const videoGrid = document.getElementById('video-list');
            videoGrid.innerHTML = `
                <div class="empty-state" style="grid-column:1/-1">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="2" y="2" width="20" height="20" rx="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/><line x1="17" y1="17" x2="22" y2="17"/></svg>
                    <div class="empty-state-title">暂无视频文件</div>
                    <div class="empty-state-text">请先在下载中心下载视频</div>
                </div>`;
            return;
        }

        const hasActiveJobs = Object.values(analysisJobs).some(s => s === 'pending' || s === 'processing');

        const videoGrid = document.getElementById('video-list');
        if (hasActiveJobs) {
            const progressDiv = document.createElement('div');
            progressDiv.id = 'analysis-progress';
            progressDiv.className = 'analysis-progress active';
            videoGrid.parentNode.insertBefore(progressDiv, videoGrid);
        }

        renderVideoList(videos, analyzedSet, analysisJobs);

        if (hasActiveJobs) startAnalysisPolling(folderName);
    } catch (e) {
        content.innerHTML = `<div class="empty-state"><p style="color:var(--red)">加载失败: ${e.message}</p></div>`;
    }
}

function renderVideoList(videos, analyzedSet, analysisJobs) {
    const videoList = document.getElementById('video-list');
    if (!videoList) return;

    videoList.innerHTML = videos.map((v, i) => {
        const stem = v.name.replace('.mp4', '');
        const hasAnalysis = analyzedSet.has(stem);
        const jobStatus = analysisJobs[stem];
        let status = 'unanalyzed';
        let badge = '<span class="badge badge-warning">未分析</span>';
        if (hasAnalysis) {
            status = 'analyzed';
            badge = '<span class="badge badge-success">已分析</span>';
        } else if (jobStatus === 'failed') {
            status = 'failed';
            badge = '<span class="badge badge-danger">失败</span>';
        } else if (jobStatus === 'processing') {
            status = 'processing';
            badge = '<span class="badge badge-info">分析中</span>';
        } else if (jobStatus === 'pending') {
            status = 'pending';
            badge = '<span class="badge badge-warning">等待中</span>';
        }
        return `
            <div class="card card-clickable video-card"
                 data-status="${status}" data-stem="${stem}"
                 style="animation:pageIn 0.25s ease ${i * 40}ms both"
                 onclick="toggleReport('${currentFolder}', '${stem}', this)">
                <div class="video-card-top">
                    <span class="video-name">${v.name}</span>
                    ${badge}
                </div>
                <div class="video-size">${(v.size / 1024 / 1024).toFixed(1)} MB</div>
            </div>`;
    }).join('');
}

function refreshVideoList(data) {
    const videos = data.videos || [];
    const analysis = data.analysis || [];
    const analysisJobs = data.analysis_jobs || {};
    const analyzedSet = new Set(analysis.map(a => a.name.replace('.md', '')));

    const progressBar = document.getElementById('analysis-progress');
    if (progressBar) {
        const total = videos.length;
        const done = videos.filter(v => analyzedSet.has(v.name.replace('.mp4', ''))).length;
        const failed = Object.values(analysisJobs).filter(s => s === 'failed').length;
        const active = Object.values(analysisJobs).filter(s => s === 'pending' || s === 'processing').length;
        const pct = total > 0 ? Math.round((done / total) * 100) : 0;
        progressBar.innerHTML = `
            <div class="analysis-progress-header">
                <span class="analysis-progress-label">分析进度</span>
                <span class="analysis-progress-count">${done}/${total}</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
            ${active > 0 ? `<p class="analysis-progress-detail">${active} 个任务进行中...</p>` : ''}
            ${failed > 0 ? `<p class="analysis-progress-detail analysis-progress-error">${failed} 个任务失败</p>` : ''}
        `;
        if (active === 0) {
            setTimeout(() => progressBar.classList.remove('active'), 3000);
        }
    }

    renderVideoList(videos, analyzedSet, analysisJobs);
}

async function toggleReport(folderName, stem, cardEl) {
    const container = document.getElementById('report-container');
    if (expandedStem === stem) {
        collapseReport();
        return;
    }

    expandedStem = stem;
    document.querySelectorAll('.video-card').forEach(c => {
        c.classList.remove('expanded');
        if (c.dataset.stem !== stem) c.style.opacity = '0.5';
        else { c.classList.add('expanded'); c.style.opacity = '1'; }
    });
    document.getElementById('video-list').classList.add('has-report');

    container.innerHTML = `
        <div class="report-panel">
            <div class="report-header">
                <span class="report-filename">${stem}.mp4</span>
                <button class="btn-icon" onclick="collapseReport()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            <div style="padding:24px"><div class="skeleton" style="height:120px"></div></div>
        </div>
    `;

    try {
        const data = await API.get(`/api/files/${folderName}/analysis/${stem}.md`);
        renderReport(data.content, stem);
    } catch (e) {
        container.innerHTML = `
            <div class="report-panel">
                <div class="report-header">
                    <span class="report-filename">${stem}.mp4</span>
                    <button class="btn-icon" onclick="collapseReport()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div style="padding:40px 24px;text-align:center">
                    <div style="color:var(--gray-400);font-size:14px;margin-bottom:16px">暂无分析报告</div>
                    <button class="btn btn-primary" onclick="analyzeOne('${folderName}', '${stem}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                        生成分析
                    </button>
                </div>
            </div>`;
    }
}

function collapseReport() {
    expandedStem = null;
    document.querySelectorAll('.video-card').forEach(c => {
        c.classList.remove('expanded');
        c.style.opacity = '';
    });
    document.getElementById('video-list').classList.remove('has-report');
    document.getElementById('report-container').innerHTML = '';
}

function cleanMarkdown(text) {
    return text.replace(/^```(?:markdown)?\s*\n?/i, '').replace(/\n?```\s*$/i, '').trim();
}

function renderMarkdown(text) {
    const cleaned = cleanMarkdown(text);
    try {
        if (typeof marked !== 'undefined') return marked.parse(cleaned);
    } catch (e) {
        console.warn('marked failed:', e);
    }
    const lines = cleaned.split('\n');
    const html = [];
    let inList = false;
    for (const line of lines) {
        let l = line
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>');
        if (/^### /.test(l)) { if (inList) { html.push('</ul>'); inList = false; } html.push('<h3>' + l.slice(4) + '</h3>'); }
        else if (/^## /.test(l)) { if (inList) { html.push('</ul>'); inList = false; } html.push('<h2>' + l.slice(3) + '</h2>'); }
        else if (/^# /.test(l)) { if (inList) { html.push('</ul>'); inList = false; } html.push('<h1>' + l.slice(2) + '</h1>'); }
        else if (/^(\*|\d+\.) /.test(l)) {
            if (!inList) { html.push('<ul>'); inList = true; }
            html.push('<li>' + l.replace(/^(\*|\d+\.) /, '') + '</li>');
        }
        else if (l.trim() === '') { if (inList) { html.push('</ul>'); inList = false; } }
        else { if (inList) { html.push('</ul>'); inList = false; } html.push('<p>' + l + '</p>'); }
    }
    if (inList) html.push('</ul>');
    return html.join('\n');
}

function splitMarkdownSections(markdown) {
    const cleaned = cleanMarkdown(markdown);
    const lines = cleaned.split('\n');
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
    if (current.length > 0) sections.push(current.join('\n'));
    return sections.length < 2 ? [cleaned] : sections;
}

function renderReport(markdown, stem) {
    const sections = splitMarkdownSections(markdown);
    const container = document.getElementById('report-container');
    const allText = sections.join(' ').toLowerCase();
    const isFull = allText.includes('rubric') || allText.includes('爆款预测') || allText.includes('综合得分');

    let tabs;
    if (sections.length <= 2) {
        tabs = [{ label: '报告', sections: [0] }];
    } else if (isFull && sections.length >= 6) {
        tabs = [
            { label: '摘要', sections: [0, 1, 2] },
            { label: '评分', sections: [3, 4] },
            { label: '预测', sections: [5] },
            { label: '建议', sections: [6] },
            { label: '亮点', sections: [7] },
        ];
    } else {
        tabs = [
            { label: '摘要', sections: [0, 1] },
            { label: '观点', sections: [2] },
            { label: '结构', sections: [3] },
            { label: '亮点', sections: [4] },
        ];
    }

    const tabButtons = tabs.length > 1 ? tabs.map((t, i) =>
        `<button class="report-tab ${i === 0 ? 'active' : ''}" onclick="switchReportTab(this, ${i})">${t.label}</button>`
    ).join('') : '';

    const tabContents = tabs.map((t, i) => {
        const content = t.sections
            .filter(idx => idx < sections.length)
            .map(idx => sections[idx])
            .join('\n\n');
        return `<div class="report-content tab-panel" style="display:${i === 0 ? 'block' : 'none'}">${renderMarkdown(content)}</div>`;
    }).join('');

    container.innerHTML = `
        <div class="report-panel">
            <div class="report-header">
                <span class="report-filename">${stem}.mp4</span>
                <button class="btn-icon" onclick="collapseReport()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            ${tabButtons ? `<div class="report-tabs">${tabButtons}</div>` : ''}
            ${tabContents}
        </div>
    `;
}

function switchReportTab(btn, index) {
    const panel = btn.closest('.report-panel');
    panel.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    panel.querySelectorAll('.tab-panel').forEach((p, i) => {
        p.style.display = i === index ? 'block' : 'none';
        if (i === index) {
            p.style.animation = 'none';
            p.offsetHeight;
            p.style.animation = 'tabFade 0.15s ease';
        }
    });
}

async function analyzeOne(folderName, stem) {
    const mode = document.getElementById('analysis-mode')?.value || 'summary';
    try {
        await API.post('/api/analysis/start', {
            video_path: `../materials/${folderName}/videos/${stem}.mp4`,
            mode,
        });
        showToast('分析任务已创建', 'success');
        collapseReport();
        startAnalysisPolling(folderName);
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
        if (!account) { showToast('未找到对应博主', 'error'); return; }

        const result = await API.post('/api/analysis/batch', { account_id: account.id, mode });
        showToast(`已创建 ${result.created} 个分析任务`, 'success');
        startAnalysisPolling(currentFolder);
    } catch (e) {
        showToast('批量分析失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '批量分析';
    }
}

function startAnalysisPolling(folderName) {
    stopAnalysisPolling();
    analysisPollingTimer = setInterval(async () => {
        try {
            const data = await API.get(`/api/files/${folderName}`);
            const jobs = data.analysis_jobs || {};
            const hasActive = Object.values(jobs).some(s => s === 'pending' || s === 'processing');
            if (!hasActive) {
                stopAnalysisPolling();
                showToast('分析完成', 'success');
            }
            if (currentFolder === folderName) refreshVideoList(data);
        } catch (e) { /* ignore */ }
    }, 3000);
}

function stopAnalysisPolling() {
    if (analysisPollingTimer) { clearInterval(analysisPollingTimer); analysisPollingTimer = null; }
}
