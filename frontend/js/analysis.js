let currentFolder = null;

async function loadAnalysis() {
    const container = document.getElementById('page-analysis');
    container.innerHTML = `
        <h1 style="margin-bottom: 20px;">分析工作台</h1>
        <div class="flex gap-16" style="align-items: flex-start;">
            <div style="width: 280px; flex-shrink: 0;">
                <h3 style="margin-bottom: 12px;">选择博主</h3>
                <div id="analysis-accounts"></div>
            </div>
            <div style="flex: 1;">
                <div id="analysis-content">
                    <p style="color: var(--text-dim);">← 请先选择博主</p>
                </div>
            </div>
        </div>
    `;

    try {
        const accounts = await API.get('/api/accounts');
        const list = document.getElementById('analysis-accounts');
        list.innerHTML = accounts.map(acc => `
            <div class="card" style="cursor: pointer; padding: 12px;" onclick="loadAccountAnalysis('${acc.folder_name}')">
                <span class="badge badge-${acc.platform}">${acc.platform === 'douyin' ? '抖音' : 'TikTok'}</span>
                <span style="margin-left: 8px;">${acc.nickname}</span>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load accounts:', e);
    }
}

async function loadAccountAnalysis(folderName) {
    currentFolder = folderName;
    const content = document.getElementById('analysis-content');
    content.innerHTML = '<p>加载中...</p>';

    try {
        const data = await API.get(`/api/files/${folderName}`);
        const videos = data.videos || [];
        const analysis = data.analysis || [];
        const analyzedSet = new Set(analysis.map(a => a.name.replace('.md', '')));

        content.innerHTML = `
            <div class="flex flex-between" style="margin-bottom: 16px;">
                <h2>${folderName}</h2>
                <div class="flex gap-8">
                    <select id="analysis-mode" style="width: auto;">
                        <option value="summary">摘要模式</option>
                        <option value="full">Full 分析</option>
                    </select>
                    <button class="btn btn-primary" onclick="batchAnalyze()">批量分析</button>
                </div>
            </div>
            <div class="grid grid-2" id="video-list">
                ${videos.map(v => {
                    const stem = v.name.replace('.mp4', '');
                    const hasAnalysis = analyzedSet.has(stem);
                    return `
                        <div class="card" style="cursor: pointer;" onclick="viewAnalysis('${folderName}', '${stem}')">
                            <div class="flex flex-between">
                                <span>${v.name}</span>
                                ${hasAnalysis ? '<span class="badge badge-success">已分析</span>' : '<span class="badge badge-warning">未分析</span>'}
                            </div>
                            <p style="font-size: 12px; color: var(--text-dim); margin-top: 4px;">
                                ${(v.size / 1024 / 1024).toFixed(1)} MB
                            </p>
                        </div>
                    `;
                }).join('')}
            </div>
            <div id="analysis-viewer" class="card mt-16" style="display: none;"></div>
        `;
    } catch (e) {
        content.innerHTML = `<p style="color: var(--danger);">加载失败: ${e.message}</p>`;
    }
}

async function viewAnalysis(folderName, stem) {
    const viewer = document.getElementById('analysis-viewer');
    viewer.style.display = 'block';
    viewer.innerHTML = '<p>加载中...</p>';

    try {
        const data = await API.get(`/api/files/${folderName}/analysis/${stem}.md`);
        viewer.innerHTML = `<div style="white-space: pre-wrap; font-size: 14px; line-height: 1.6;">${marked(data.content)}</div>`;
    } catch (e) {
        viewer.innerHTML = `
            <p style="color: var(--text-dim);">暂无分析报告</p>
            <button class="btn btn-primary mt-16" onclick="analyzeOne('${folderName}', '${stem}')">生成分析</button>
        `;
    }
}

async function analyzeOne(folderName, stem) {
    const mode = document.getElementById('analysis-mode')?.value || 'summary';
    try {
        await API.post('/api/analysis/start', {
            video_path: `../materials/${folderName}/videos/${stem}.mp4`,
            mode,
        });
        alert('分析任务已创建，请稍后刷新查看结果');
    } catch (e) {
        alert('分析失败: ' + e.message);
    }
}

async function batchAnalyze() {
    if (!currentFolder) return;
    const mode = document.getElementById('analysis-mode')?.value || 'summary';

    try {
        const accounts = await API.get('/api/accounts');
        const account = accounts.find(a => a.folder_name === currentFolder);
        if (!account) { alert('未找到对应博主'); return; }

        await API.post('/api/analysis/batch', {
            account_id: account.id,
            mode,
        });
        alert('批量分析任务已创建');
    } catch (e) {
        alert('批量分析失败: ' + e.message);
    }
}
