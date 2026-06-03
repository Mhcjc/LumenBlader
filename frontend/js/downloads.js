let pollInterval = null;
let currentTaskFilter = 'all';

function isCookieError(msg) {
    const keywords = ['cookie', 'Cookie', 'JSON', '超时', 'timeout', '502', '获取视频详情失败', '无法连接'];
    return keywords.some(k => msg.includes(k));
}

function getTimeAgo(dateStr) {
    const now = new Date();
    const date = new Date(dateStr);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins} 分钟前`;
    if (diffHours < 24) return `${diffHours} 小时前`;
    return `${diffDays} 天前`;
}

function renderDownloadStats(jobs) {
    const container = document.getElementById('download-stats');
    if (!container) return;
    const total = jobs.length;
    const completed = jobs.filter(j => j.status === 'completed').length;
    const downloading = jobs.filter(j => j.status === 'downloading' || j.status === 'pending').length;
    const failed = jobs.filter(j => j.status === 'failed').length;
    container.innerHTML = `
        <div class="stat-card stat-card--blue">
            <div class="stat-card-value">${total}</div>
            <div class="stat-card-label">总任务数</div>
        </div>
        <div class="stat-card stat-card--green">
            <div class="stat-card-value">${completed}</div>
            <div class="stat-card-label">已完成</div>
        </div>
        <div class="stat-card stat-card--orange">
            <div class="stat-card-value">${downloading}</div>
            <div class="stat-card-label">进行中</div>
        </div>
        <div class="stat-card stat-card--red">
            <div class="stat-card-value">${failed}</div>
            <div class="stat-card-label">失败</div>
        </div>`;
}

function filterTasks(filter) {
    currentTaskFilter = filter;
    document.querySelectorAll('.download-filter-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.filter === filter);
    });
    const jobs = window._downloadJobs || [];
    renderTaskList(jobs);
}

async function loadDownloads() {
    const container = document.getElementById('page-downloads');
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">下载中心</h1>
                <p class="page-subtitle">管理视频下载任务，实时追踪进度</p>
            </div>
        </div>
        <div id="download-stats" class="download-stats"></div>
        <div class="download-single">
            <div class="download-single-title">单视频下载</div>
            <div class="download-single-desc">粘贴视频链接，快速下载单个视频</div>
            <div class="download-single-inner">
                <input type="text" class="input" id="single-url" placeholder="粘贴抖音或 TikTok 视频链接…">
                <button class="btn btn-primary" id="single-download-btn" onclick="submitSingleDownload()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    下载
                </button>
            </div>
        </div>
        <div class="download-filter">
            <div class="download-filter-tabs" id="download-filter-tabs">
                <button class="download-filter-tab active" data-filter="all" onclick="filterTasks('all')">全部</button>
                <button class="download-filter-tab" data-filter="downloading" onclick="filterTasks('downloading')">下载中</button>
                <button class="download-filter-tab" data-filter="completed" onclick="filterTasks('completed')">已完成</button>
                <button class="download-filter-tab" data-filter="failed" onclick="filterTasks('failed')">失败</button>
            </div>
        </div>
        <div id="download-jobs" class="task-list"></div>
    `;
    await refreshDownloadJobs();
}

async function refreshDownloadJobs() {
    try {
        const jobs = await API.get('/api/downloads');
        window._downloadJobs = jobs || [];
        renderDownloadStats(window._downloadJobs);
        renderTaskList(window._downloadJobs);
    } catch (e) {
        console.error('Failed to load jobs:', e);
    }
}

function renderTaskList(jobs) {
    const container = document.getElementById('download-jobs');
    if (!container) return;

    if (!jobs || jobs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <div class="empty-state-title">暂无下载任务</div>
                <div class="empty-state-text">粘贴视频链接或从博主页面批量下载</div>
            </div>`;
        return;
    }

    const filtered = currentTaskFilter === 'all'
        ? jobs
        : jobs.filter(j => {
            if (currentTaskFilter === 'downloading') return j.status === 'downloading' || j.status === 'pending';
            return j.status === currentTaskFilter;
        });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-title">没有匹配的任务</div>
                <div class="empty-state-text">当前筛选条件下没有任务</div>
            </div>`;
        return;
    }

    container.innerHTML = filtered.map(job => {
        const pct = job.total_videos > 0 ? Math.round((job.downloaded / job.total_videos) * 100) : 0;
        const statusMap = {
            pending: { badge: 'badge-warning', label: '等待中' },
            downloading: { badge: 'badge-info', label: '下载中' },
            completed: { badge: 'badge-success', label: '已完成' },
            failed: { badge: 'badge-danger', label: `失败 ${job.failed}` },
            cancelled: { badge: 'badge-warning', label: '已取消' },
        };
        const s = statusMap[job.status] || statusMap.pending;
        const isActive = job.status === 'pending' || job.status === 'downloading';
        const dateRange = job.earliest && job.latest
            ? `${job.earliest.replace(/-/g, '/')} — ${job.latest.replace(/-/g, '/')}`
            : '全部视频';
        const timeAgo = job.created_at ? getTimeAgo(job.created_at) : '';

        const items = job.items || [];
        const videoTitle = items.length === 1
            ? (items[0].title || items[0].video_id)
            : (items.length > 1 ? `${items.length} 个视频` : '');

        return `
            <div class="card task-card">
                <div class="task-header">
                    <div class="task-header-left">
                        <div style="display:flex;align-items:center;gap:8px">
                            ${job.platform ? `<span class="badge badge-${job.platform}" style="font-size:9px;padding:1px 5px">${job.platform === 'douyin' ? '抖音' : 'TK'}</span>` : ''}
                            <span class="task-account">${job.account_name || '未知博主'}</span>
                        </div>
                        ${videoTitle ? `<span class="task-video-title" title="${videoTitle}">${videoTitle}</span>` : ''}
                    </div>
                    <div class="task-header-right">
                        <span class="badge ${s.badge}">${s.label}</span>
                        ${isActive
                            ? `<button class="btn btn-secondary btn-sm" onclick="cancelJob('${job.id}')">取消</button>`
                            : `<button class="btn-icon btn-icon-danger" onclick="deleteJob('${job.id}')" title="删除">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                               </button>`
                        }
                    </div>
                </div>
                <div class="task-info">
                    <span class="task-info-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                        ${dateRange}
                    </span>
                    ${timeAgo ? `<span class="task-info-item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        ${timeAgo}
                    </span>` : ''}
                </div>
                <div class="task-progress-row">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:${pct}%;${job.status === 'failed' ? 'background:var(--red)' : ''}"></div>
                    </div>
                    <span class="task-progress-pct">${pct}%</span>
                </div>
                <div class="task-actions">
                    <button class="btn btn-secondary btn-sm" onclick="viewJobDetail('${job.id}')">查看详情</button>
                    ${job.failed > 0 && !isActive ? `<button class="btn btn-primary btn-sm" onclick="retryFailed('${job.id}')">重试失败项</button>` : ''}
                </div>
            </div>`;
    }).join('');
}

async function submitSingleDownload() {
    const url = document.getElementById('single-url').value.trim();
    if (!url) { showToast('请输入链接', 'error'); return; }

    const platform = (url.includes('douyin.com') || url.includes('iesdouyin.com')) ? 'douyin' : 'tiktok';
    await callWithCookieCheck(platform, async () => {
        const btn = document.getElementById('single-download-btn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 下载中';

        try {
            await API.post('/api/downloads/single', { url });
            document.getElementById('single-url').value = '';
            showToast('下载任务已创建', 'success');
            refreshDownloadJobs();
            startDownloadPolling();
        } catch (e) {
            showToast('下载失败: ' + e.message, 'error');
            if (isCookieError(e.message)) {
                showToast('可能是 Cookie 已失效，请在设置中更新', 'error');
                if (typeof checkCookieHealth === 'function') checkCookieHealth();
            }
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> 下载';
        }
    });
}

function startDownloadPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(() => refreshDownloadJobs(), 3000);
    setTimeout(() => stopDownloadPolling(), 600000);
}

function stopDownloadPolling() {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
}

async function cancelJob(jobId) {
    try {
        await API.post(`/api/downloads/${jobId}/cancel`);
        showToast('任务已取消', 'success');
        refreshDownloadJobs();
    } catch (e) {
        showToast('取消失败: ' + e.message, 'error');
    }
}

async function deleteJob(jobId) {
    if (!confirm('确定删除该下载任务？')) return;
    try {
        await API.del(`/api/downloads/${jobId}`);
        showToast('任务已删除', 'success');
        refreshDownloadJobs();
    } catch (e) {
        showToast('删除失败: ' + e.message, 'error');
    }
}

async function retryFailed(jobId) {
    const job = (window._downloadJobs || []).find(j => j.id === jobId);
    const platform = job ? (job.platform || 'douyin') : 'douyin';
    await callWithCookieCheck(platform, async () => {
        try {
            const result = await API.post(`/api/downloads/${jobId}/retry`);
            showToast(`正在重试 ${result.retrying} 个失败项...`, 'success');
            refreshDownloadJobs();
            startDownloadPolling();
        } catch (e) {
            showToast('重试失败: ' + e.message, 'error');
        }
    });
}

async function viewJobDetail(jobId) {
    try {
        const job = await API.get(`/api/downloads/${jobId}`);
        const items = await API.get(`/api/downloads/${jobId}/items`);
        const statusMap = { completed: '已完成', failed: '失败', downloading: '下载中', pending: '等待中', cancelled: '已取消' };
        const badgeMap = { completed: 'badge-success', failed: 'badge-danger', downloading: 'badge-info', pending: 'badge-warning', cancelled: 'badge-warning' };
        const pct = job.total_videos > 0 ? Math.round((job.downloaded / job.total_videos) * 100) : 0;

        const itemsHtml = items.map(item => `
            <div class="detail-item">
                <div class="detail-item-title">${item.title || item.video_id}</div>
                <div class="detail-item-row">
                    <span class="badge ${badgeMap[item.status] || 'badge-warning'}">${statusMap[item.status] || item.status}</span>
                    ${item.status === 'failed' ? `<button class="btn btn-primary btn-sm" onclick="retryItem('${jobId}', '${item.id}')" style="font-size:11px;padding:2px 8px">重试</button>` : ''}
                </div>
                ${item.error ? `<p class="detail-item-error">${item.error}</p>` : ''}
            </div>
        `).join('');

        document.getElementById('task-detail-body').innerHTML = `
            <div class="detail-summary">
                <div class="detail-summary-row">
                    <span class="detail-label">博主</span>
                    <span class="detail-value">
                        ${job.platform ? `<span class="badge badge-${job.platform}" style="font-size:9px;padding:1px 5px;margin-right:6px">${job.platform === 'douyin' ? '抖音' : 'TK'}</span>` : ''}
                        ${job.account_name || '未知博主'}
                    </span>
                </div>
                <div class="detail-summary-row">
                    <span class="detail-label">状态</span>
                    <span class="badge ${badgeMap[job.status] || 'badge-warning'}">${statusMap[job.status] || job.status}</span>
                </div>
                <div class="detail-summary-row">
                    <span class="detail-label">进度</span>
                    <span class="detail-value">${job.downloaded}/${job.total_videos} (${pct}%)</span>
                </div>
                <div class="detail-summary-row">
                    <span class="detail-label">创建时间</span>
                    <span class="detail-value">${job.created_at ? new Date(job.created_at).toLocaleString('zh-CN') : '-'}</span>
                </div>
                ${job.finished_at ? `<div class="detail-summary-row">
                    <span class="detail-label">完成时间</span>
                    <span class="detail-value">${new Date(job.finished_at).toLocaleString('zh-CN')}</span>
                </div>` : ''}
            </div>
            <div class="detail-items-header">下载项</div>
            <div class="detail-items">${itemsHtml || '<div style="padding:16px 0;color:var(--gray-400);font-size:13px">暂无下载项</div>'}</div>
        `;
        openModal('task-detail-overlay');
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

function closeTaskDetail() {
    closeModal('task-detail-overlay');
}

async function retryItem(jobId, itemId) {
    const job = (window._downloadJobs || []).find(j => j.id === jobId);
    const platform = job ? (job.platform || 'douyin') : 'douyin';
    await callWithCookieCheck(platform, async () => {
        try {
            await API.post(`/api/downloads/${jobId}/retry`);
            showToast('正在重试...', 'success');
            viewJobDetail(jobId);
            refreshDownloadJobs();
            startDownloadPolling();
        } catch (e) {
            showToast('重试失败: ' + e.message, 'error');
        }
    });
}
