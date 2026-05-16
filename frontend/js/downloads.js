let pollInterval = null;

async function loadDownloads() {
    const container = document.getElementById('page-downloads');
    container.innerHTML = `
        <h1 style="margin-bottom: 20px;">下载中心</h1>
        <div class="card">
            <h3>单视频下载</h3>
            <div class="flex gap-8 mt-16">
                <input type="text" id="single-url" placeholder="粘贴视频链接">
                <button class="btn btn-primary" onclick="submitSingleDownload()">下载</button>
            </div>
        </div>
        <h2 style="margin: 24px 0 16px;">下载任务</h2>
        <div id="download-jobs"></div>
    `;
    await refreshDownloadJobs();
}

async function refreshDownloadJobs() {
    try {
        const jobs = await API.get('/api/downloads');
        const container = document.getElementById('download-jobs');

        if (!jobs || jobs.length === 0) {
            container.innerHTML = '<p style="color: var(--text-dim);">暂无下载任务</p>';
            return;
        }

        container.innerHTML = jobs.map(job => {
            const pct = job.total_videos > 0 ? Math.round((job.downloaded / job.total_videos) * 100) : 0;
            const statusBadge = {
                pending: 'badge-warning',
                downloading: 'badge-warning',
                completed: 'badge-success',
                failed: 'badge-danger',
            }[job.status] || 'badge-warning';

            return `
                <div class="card">
                    <div class="flex flex-between">
                        <span>任务 ${job.id.slice(0, 8)}</span>
                        <span class="badge ${statusBadge}">${job.status}</span>
                    </div>
                    <div class="flex flex-between mt-16" style="font-size: 13px; color: var(--text-dim);">
                        <span>时间范围: ${job.earliest || '最早'} ~ ${job.latest || '最新'}</span>
                        <span>${job.downloaded}/${job.total_videos} 已下载, ${job.failed} 失败</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${pct}%"></div>
                    </div>
                    <button class="btn btn-secondary mt-16" onclick="viewJobItems('${job.id}')">查看详情</button>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed to load jobs:', e);
    }
}

async function submitSingleDownload() {
    const url = document.getElementById('single-url').value.trim();
    if (!url) { alert('请输入链接'); return; }

    try {
        await API.post('/api/downloads/single', { url });
        document.getElementById('single-url').value = '';
        refreshDownloadJobs();
    } catch (e) {
        alert('下载失败: ' + e.message);
    }
}

async function triggerBatchDownload(accountId) {
    const earliest = prompt('起始日期 (留空不限, 格式: 2025-01-01):') || '';
    const latest = prompt('结束日期 (留空不限, 格式: 2025-12-31):') || '';

    try {
        await API.post('/api/downloads/batch', { account_id: accountId, earliest, latest });
        refreshDownloadJobs();
        startPolling();
    } catch (e) {
        alert('批量下载失败: ' + e.message);
    }
}

function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(() => {
        refreshDownloadJobs();
    }, 3000);
    setTimeout(() => { stopPolling(); }, 300000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function viewJobItems(jobId) {
    try {
        const items = await API.get(`/api/downloads/${jobId}/items`);
        const html = items.map(item => `
            <div class="flex flex-between" style="padding: 8px 0; border-bottom: 1px solid var(--border);">
                <span>${item.title || item.video_id}</span>
                <span class="badge ${item.status === 'completed' ? 'badge-success' : item.status === 'failed' ? 'badge-danger' : 'badge-warning'}">${item.status}</span>
            </div>
        `).join('');

        const modal = document.getElementById('settings-modal');
        const form = document.getElementById('settings-form');
        modal.classList.remove('hidden');
        modal.querySelector('h2').textContent = '下载详情';
        form.innerHTML = html || '<p>暂无下载项</p>';
    } catch (e) {
        alert('加载失败: ' + e.message);
    }
}
