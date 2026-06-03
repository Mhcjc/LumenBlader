async function loadSettings() {
    const form = document.getElementById('settings-form');
    form.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto"></div></div>';

    try {
        const settings = await API.get('/api/settings');
        const cookieDy = settings.tiktok_downloader.cookie_douyin || '';
        const cookieTt = settings.tiktok_downloader.cookie_tiktok || '';

        form.innerHTML = `
            <div class="section-label">TikTokDownloader</div>
            <div class="form-group">
                <label class="form-label">API 地址</label>
                <input type="text" class="input" id="s-ttd-url" value="${settings.tiktok_downloader.api_base_url}">
            </div>
            <div class="form-group">
                <label class="form-label">抖音 Cookie</label>
                <div class="input-with-toggle">
                    <input type="password" class="input" id="s-ttd-cookie-dy" value="${cookieDy}" placeholder="粘贴抖音 Cookie">
                    <button class="toggle-visibility" onclick="togglePassword('s-ttd-cookie-dy')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                </div>
                <p class="form-hint">${cookieDy.length > 0 ? cookieDy.length + ' 字符' : '未设置'}</p>
            </div>
            <div class="form-group">
                <label class="form-label">TikTok Cookie</label>
                <div class="input-with-toggle">
                    <input type="password" class="input" id="s-ttd-cookie-tt" value="${cookieTt}" placeholder="粘贴 TikTok Cookie">
                    <button class="toggle-visibility" onclick="togglePassword('s-ttd-cookie-tt')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                </div>
                <p class="form-hint">${cookieTt.length > 0 ? cookieTt.length + ' 字符' : '未设置'}</p>
            </div>
            <div class="form-group">
                <label class="form-label">代理</label>
                <input type="text" class="input" id="s-ttd-proxy" value="${settings.tiktok_downloader.proxy}" placeholder="http://127.0.0.1:7890">
            </div>

            <hr class="divider">
            <div class="section-label">AI 分析</div>
            <div class="form-group">
                <label class="form-label">API Key</label>
                <div class="input-with-toggle">
                    <input type="password" class="input" id="s-ai-key" value="${settings.ai.api_key}" placeholder="sk-...">
                    <button class="toggle-visibility" onclick="togglePassword('s-ai-key')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    </button>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Base URL</label>
                <input type="text" class="input" id="s-ai-url" value="${settings.ai.base_url}">
            </div>
            <div class="form-group">
                <label class="form-label">模型</label>
                <input type="text" class="input" id="s-ai-model" value="${settings.ai.model}">
            </div>

            <hr class="divider">
            <div class="section-label">服务器</div>
            <div class="form-group">
                <label class="form-label">端口</label>
                <input type="number" class="input" id="s-port" value="${settings.server.port}">
            </div>
        `;

        const modal = form.closest('.modal');
        let footer = modal.querySelector('.modal-footer');
        if (!footer) {
            footer = document.createElement('div');
            footer.className = 'modal-footer';
            modal.appendChild(footer);
        }
        footer.innerHTML = `
            <button class="btn btn-secondary" onclick="closeModal('settings-overlay')">取消</button>
            <button class="btn btn-primary" onclick="saveSettings()">保存设置</button>
        `;
    } catch (e) {
        form.innerHTML = `<div class="empty-state"><p style="color:var(--red)">加载失败: ${e.message}</p></div>`;
        const modal = form.closest('.modal');
        const footer = modal.querySelector('.modal-footer');
        if (footer) footer.innerHTML = '';
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
        showToast('设置已保存', 'success');
        closeModal('settings-overlay');
        // Invalidate cookie health cache so next request re-checks
        localStorage.removeItem('cookie_health_cache');
        if (typeof checkCookieHealth === 'function') checkCookieHealth();
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}
