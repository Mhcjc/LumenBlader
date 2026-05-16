async function loadSettings() {
    const form = document.getElementById('settings-form');
    form.innerHTML = '<p>加载中...</p>';

    try {
        const settings = await API.get('/api/settings');
        form.innerHTML = `
            <h3 style="margin-bottom: 12px;">TikTokDownloader</h3>
            <div class="form-group">
                <label>API 地址</label>
                <input type="text" id="s-ttd-url" value="${settings.tiktok_downloader.api_base_url}">
            </div>
            <div class="form-group">
                <label>抖音 Cookie</label>
                <input type="text" id="s-ttd-cookie-dy" value="${settings.tiktok_downloader.cookie_douyin}" placeholder="粘贴抖音 Cookie">
            </div>
            <div class="form-group">
                <label>TikTok Cookie</label>
                <input type="text" id="s-ttd-cookie-tt" value="${settings.tiktok_downloader.cookie_tiktok}" placeholder="粘贴 TikTok Cookie">
            </div>
            <div class="form-group">
                <label>代理</label>
                <input type="text" id="s-ttd-proxy" value="${settings.tiktok_downloader.proxy}" placeholder="http://127.0.0.1:7890">
            </div>

            <h3 style="margin: 20px 0 12px;">AI 分析</h3>
            <div class="form-group">
                <label>API Key</label>
                <input type="password" id="s-ai-key" value="${settings.ai.api_key}" placeholder="sk-...">
            </div>
            <div class="form-group">
                <label>Base URL</label>
                <input type="text" id="s-ai-url" value="${settings.ai.base_url}">
            </div>
            <div class="form-group">
                <label>模型</label>
                <input type="text" id="s-ai-model" value="${settings.ai.model}">
            </div>

            <h3 style="margin: 20px 0 12px;">服务器</h3>
            <div class="form-group">
                <label>端口</label>
                <input type="number" id="s-port" value="${settings.server.port}">
            </div>

            <button class="btn btn-primary mt-16" onclick="saveSettings()">保存</button>
        `;
    } catch (e) {
        form.innerHTML = `<p style="color: var(--danger);">加载失败: ${e.message}</p>`;
    }
}

async function saveSettings() {
    const data = {
        tiktok_downloader: {
            api_base_url: document.getElementById('s-ttd-url').value,
            cookie_douyin: document.getElementById('s-ttd-cookie-dy').value,
            cookie_tiktok: document.getElementById('s-ttd-cookie-tt').value,
            proxy: document.getElementById('s-ttd-proxy').value,
        },
        ai: {
            api_key: document.getElementById('s-ai-key').value,
            base_url: document.getElementById('s-ai-url').value,
            model: document.getElementById('s-ai-model').value,
        },
        server: {
            port: parseInt(document.getElementById('s-port').value),
        },
    };

    try {
        await API.patch('/api/settings', data);
        alert('设置已保存');
        document.getElementById('settings-modal').classList.add('hidden');
    } catch (e) {
        alert('保存失败: ' + e.message);
    }
}
