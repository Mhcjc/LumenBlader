async function loadAccounts() {
    const container = document.getElementById('page-accounts');
    container.innerHTML = `
        <div class="flex flex-between" style="margin-bottom: 20px;">
            <h1>博主管理</h1>
            <button class="btn btn-primary" onclick="showAddAccountModal()">+ 添加博主</button>
        </div>
        <div id="accounts-list" class="grid grid-3"></div>
    `;

    try {
        const accounts = await API.get('/api/accounts');
        const list = document.getElementById('accounts-list');

        if (accounts.length === 0) {
            list.innerHTML = '<p class="text-center" style="grid-column: 1/-1; color: var(--text-dim);">暂无博主，点击右上角添加</p>';
            return;
        }

        list.innerHTML = accounts.map(acc => `
            <div class="card">
                <div class="flex flex-between">
                    <span class="badge badge-${acc.platform}">${acc.platform === 'douyin' ? '抖音' : 'TikTok'}</span>
                    <button class="btn-icon" onclick="deleteAccount('${acc.id}')" title="删除">&times;</button>
                </div>
                <h3 style="margin: 8px 0;">${acc.nickname}</h3>
                <p style="font-size: 12px; color: var(--text-dim); margin-bottom: 12px;">
                    ${acc.last_synced_at ? '最后同步: ' + new Date(acc.last_synced_at).toLocaleString() : '未同步'}
                </p>
                <div class="flex gap-8">
                    <button class="btn btn-primary" onclick="startBatchDownload('${acc.id}')">批量下载</button>
                    <button class="btn btn-secondary" onclick="viewAccountFiles('${acc.folder_name}')">查看内容</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML += `<p style="color: var(--danger);">加载失败: ${e.message}</p>`;
    }
}

function showAddAccountModal() {
    const modal = document.getElementById('settings-modal');
    const form = document.getElementById('settings-form');
    modal.classList.remove('hidden');
    modal.querySelector('h2').textContent = '添加博主';

    form.innerHTML = `
        <div class="form-group">
            <label>博主主页链接</label>
            <input type="text" id="add-url" placeholder="粘贴抖音或 TikTok 主页链接">
        </div>
        <div class="form-group">
            <label>平台 (留空自动识别)</label>
            <select id="add-platform">
                <option value="">自动识别</option>
                <option value="douyin">抖音</option>
                <option value="tiktok">TikTok</option>
            </select>
        </div>
        <button class="btn btn-primary" onclick="submitAddAccount()">添加</button>
    `;
}

async function submitAddAccount() {
    const url = document.getElementById('add-url').value.trim();
    const platform = document.getElementById('add-platform').value;

    if (!url) { alert('请输入链接'); return; }

    try {
        await API.post('/api/accounts', { url, platform });
        document.getElementById('settings-modal').classList.add('hidden');
        loadAccounts();
    } catch (e) {
        alert('添加失败: ' + e.message);
    }
}

async function deleteAccount(id) {
    if (!confirm('确定删除该博主？')) return;
    try {
        await API.del(`/api/accounts/${id}`);
        loadAccounts();
    } catch (e) {
        alert('删除失败: ' + e.message);
    }
}

function startBatchDownload(accountId) {
    document.querySelector('[data-page="downloads"]').click();
    if (typeof triggerBatchDownload === 'function') {
        triggerBatchDownload(accountId);
    }
}

function viewAccountFiles(folderName) {
    document.querySelector('[data-page="analysis"]').click();
    if (typeof loadAccountAnalysis === 'function') {
        loadAccountAnalysis(folderName);
    }
}
