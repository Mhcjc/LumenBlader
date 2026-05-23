function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = {
        success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
        error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        info: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
    };
    toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function openModal(id) {
    document.getElementById(id).classList.add('open');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('open');
}

function switchPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('page-' + page).classList.add('active');
    document.querySelector(`.nav-tab[data-page="${page}"]`).classList.add('active');
    if (page === 'accounts' && typeof loadAccounts === 'function') loadAccounts();
    if (page === 'downloads' && typeof loadDownloads === 'function') loadDownloads();
    if (page === 'analysis' && typeof loadAnalysis === 'function') loadAnalysis();
}

function togglePassword(id) {
    const input = document.getElementById(id);
    input.type = input.type === 'password' ? 'text' : 'password';
}

function dismissCookieBanner() {
    document.getElementById('cookie-banner').style.display = 'none';
    sessionStorage.setItem('cookie-banner-dismissed', '1');
}

async function checkCookieHealth() {
    try {
        const data = await API.get('/api/health/cookie');
        const banner = document.getElementById('cookie-banner');
        const text = document.getElementById('cookie-banner-text');
        const dismissed = sessionStorage.getItem('cookie-banner-dismissed');

        if (!data.downloader_alive) {
            text.textContent = 'TikTokDownloader 服务未运行，下载功能不可用';
            banner.style.display = '';
            sessionStorage.removeItem('cookie-banner-dismissed');
        } else if (!data.douyin) {
            text.textContent = data.message || '抖音 Cookie 已失效，下载功能可能无法正常使用';
            if (!dismissed) banner.style.display = '';
        } else {
            banner.style.display = 'none';
            sessionStorage.removeItem('cookie-banner-dismissed');
        }
    } catch (e) {
        // Health check failed silently — don't bother the user
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchPage(tab.dataset.page));
    });

    // Settings modal
    const settingsBtn = document.getElementById('settings-btn');
    const settingsOverlay = document.getElementById('settings-overlay');
    const settingsClose = document.getElementById('settings-close');

    settingsBtn.addEventListener('click', () => {
        openModal('settings-overlay');
        if (typeof loadSettings === 'function') loadSettings();
    });
    settingsClose.addEventListener('click', () => closeModal('settings-overlay'));

    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('open');
        });
    });

    // Close modals on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.open').forEach(o => o.classList.remove('open'));
        }
    });

    // Initial load
    if (typeof loadAccounts === 'function') loadAccounts();

    // Cookie health check
    checkCookieHealth();
});
