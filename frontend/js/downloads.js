let pollInterval = null;

async function loadDownloads() {
    const container = document.getElementById('page-downloads');
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">下载中心</h1>
                <p class="page-subtitle">管理视频下载任务，实时追踪进度</p>
            </div>
        </div>
        <div class="download-single">
            <div class="section-label">单视频下载</div>
            <div class="download-single-inner">
                <input type="text" class="input" id="single-url" placeholder="粘贴抖音或 TikTok 视频链接…">
                <button class="btn btn-primary" id="single-download-btn" onclick="submitSingleDownload()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    下载
                </button>
            </div>
        </div>
        <div class="section-label section-gap">下载任务</div>
        <div id="download-jobs" class="task-list"></div>
    `;
    await refreshDownloadJobs();
}

async function refreshDownloadJobs() {
    try {
        const jobs = await API.get('/api/downloads');
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

        container.innerHTML = jobs.map(job => {
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
                ? `${job.earliest.replace(/-/g, '/')} - ${job.latest.replace(/-/g, '/')}`
                : '全部视频';

            return `
                <div class="card task-card">
                    <div class="task-header">
                        <span class="task-id">${job.id.slice(0, 8)}…</span>
                        <div style="display:flex;align-items:center;gap:8px">
                            <span class="badge ${s.badge}">${s.label}</span>
                            ${isActive
                                ? `<button class="btn btn-secondary btn-sm" onclick="cancelJob('${job.id}')">取消</button>`
                                : `<button class="btn-icon btn-icon-danger" onclick="deleteJob('${job.id}')" title="删除">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                                   </button>`
                            }
                        </div>
                    </div>
                    <div class="task-meta">
                        <span>时间范围: ${dateRange}</span>
                        <span>${job.downloaded}/${job.total_videos} 已下载${job.failed > 0 ? `, ${job.failed} 失败` : ''}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width:${pct}%;${job.status === 'failed' ? 'background:var(--red)' : ''}"></div>
                    </div>
                    <div class="task-actions">
                        <button class="btn btn-secondary btn-sm" onclick="viewJobItems('${job.id}')">查看详情</button>
                        ${job.failed > 0 && !isActive ? `<button class="btn btn-primary btn-sm" onclick="retryFailed('${job.id}')">重试失败项</button>` : ''}
                    </div>
                </div>`;
        }).join('');
    } catch (e) {
        console.error('Failed to load jobs:', e);
    }
}

async function submitSingleDownload() {
    const url = document.getElementById('single-url').value.trim();
    if (!url) { showToast('请输入链接', 'error'); return; }

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
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> 下载';
    }
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
    try {
        const result = await API.post(`/api/downloads/${jobId}/retry`);
        showToast(`正在重试 ${result.retrying} 个失败项...`, 'success');
        refreshDownloadJobs();
        startDownloadPolling();
    } catch (e) {
        showToast('重试失败: ' + e.message, 'error');
    }
}

async function viewJobItems(jobId) {
    try {
        const items = await API.get(`/api/downloads/${jobId}/items`);
        const statusMap = { completed: '已完成', failed: '失败', downloading: '下载中', pending: '等待中', cancelled: '已取消' };
        const html = items.map(item => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--gray-200);font-size:13px">
                <span style="font-family:var(--font-mono);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-right:12px">${item.title || item.video_id}</span>
                <div style="display:flex;align-items:center;gap:8px">
                    <span class="badge ${item.status === 'completed' ? 'badge-success' : item.status === 'failed' ? 'badge-danger' : 'badge-warning'}">${statusMap[item.status] || item.status}</span>
                    ${item.status === 'failed' ? `<button class="btn btn-primary btn-sm" onclick="retryItem('${jobId}', '${item.id}')" style="font-size:11px;padding:2px 8px">重试</button>` : ''}
                </div>
            </div>
            ${item.error ? `<p style="color:var(--red);font-size:12px;margin:4px 0 8px">${item.error}</p>` : ''}
        `).join('');

        document.getElementById('task-detail-body').innerHTML = html || '<div class="empty-state"><p class="empty-state-text">暂无下载项</p></div>';
        openModal('task-detail-overlay');
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

function closeTaskDetail() {
    closeModal('task-detail-overlay');
}

async function retryItem(jobId, itemId) {
    try {
        await API.post(`/api/downloads/${jobId}/retry`);
        showToast('正在重试...', 'success');
        viewJobItems(jobId);
        refreshDownloadJobs();
        startDownloadPolling();
    } catch (e) {
        showToast('重试失败: ' + e.message, 'error');
    }
}
