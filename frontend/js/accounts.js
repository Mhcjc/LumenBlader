let currentBatchAccountId = null;

async function loadAccounts() {
    const container = document.getElementById('page-accounts');
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">博主管理</h1>
                <p class="page-subtitle">管理你的抖音和 TikTok 博主列表</p>
            </div>
            <button class="btn btn-primary" onclick="showAddAccountModal()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
                添加博主
            </button>
        </div>
        <div id="accounts-list" class="accounts-grid"></div>
    `;

    try {
        const accounts = await API.get('/api/accounts');
        const list = document.getElementById('accounts-list');

        if (accounts.length === 0) {
            list.innerHTML = `
                <div class="empty-state" style="grid-column:1/-1">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
                    <div class="empty-state-title">还没有博主</div>
                    <div class="empty-state-text">点击上方「添加博主」开始管理你的自媒体账号</div>
                </div>`;
            return;
        }

        list.innerHTML = accounts.map((acc, i) => `
            <div class="card account-card" style="animation: pageIn 0.25s ease ${i * 40}ms both">
                <div class="account-card-top">
                    <div class="account-card-info">
                        <span class="badge badge-${acc.platform}">${acc.platform === 'douyin' ? '抖音' : 'TikTok'}</span>
                        <div class="account-name">${acc.nickname}</div>
                        <div class="account-meta">${acc.last_synced_at ? new Date(acc.last_synced_at).toLocaleDateString('zh-CN') : '未同步'}</div>
                    </div>
                    <button class="btn-icon btn-icon-danger" onclick="deleteAccount('${acc.id}')" title="删除">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>
                    </button>
                </div>
                <div class="account-actions">
                    <button class="btn btn-primary btn-sm" onclick="startBatchDownload('${acc.id}')">批量下载</button>
                    <button class="btn btn-secondary btn-sm" onclick="viewAccountFiles('${acc.folder_name}')">查看内容</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        showToast('加载博主失败: ' + e.message, 'error');
    }
}

function showAddAccountModal() {
    document.getElementById('add-account-url').value = '';
    openModal('add-account-overlay');
}

function closeAddAccount() {
    closeModal('add-account-overlay');
}

async function submitAddAccount() {
    const url = document.getElementById('add-account-url').value.trim();
    if (!url) { showToast('请输入链接', 'error'); return; }

    try {
        await API.post('/api/accounts', { url, platform: '' });
        closeAddAccount();
        showToast('博主添加成功', 'success');
        loadAccounts();
    } catch (e) {
        showToast('添加失败: ' + e.message, 'error');
    }
}

async function deleteAccount(id) {
    if (!confirm('确定删除该博主？本地文件不会被删除。')) return;
    try {
        await API.del(`/api/accounts/${id}`);
        showToast('博主已删除', 'success');
        loadAccounts();
    } catch (e) {
        showToast('删除失败: ' + e.message, 'error');
    }
}

function startBatchDownload(accountId) {
    currentBatchAccountId = accountId;
    document.getElementById('batch-earliest').value = '';
    document.getElementById('batch-latest').value = '';
    openModal('batch-download-overlay');
}

function closeBatchDownload() {
    closeModal('batch-download-overlay');
}

async function submitBatchDownload() {
    if (!currentBatchAccountId) return;
    const earliest = document.getElementById('batch-earliest').value || '';
    const latest = document.getElementById('batch-latest').value || '';

    const btn = document.getElementById('batch-submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> 创建中';

    try {
        await API.post('/api/downloads/batch', { account_id: currentBatchAccountId, earliest, latest });
        closeBatchDownload();
        showToast('批量下载任务已创建', 'success');
        switchPage('downloads');
    } catch (e) {
        showToast('批量下载失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '开始下载';
    }
}

function viewAccountFiles(folderName) {
    switchPage('analysis');
    setTimeout(() => {
        if (typeof loadAccountAnalysis === 'function') {
            loadAccountAnalysis(folderName);
        }
    }, 100);
}
