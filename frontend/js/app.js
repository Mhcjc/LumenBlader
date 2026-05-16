document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;

            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            pages.forEach(p => p.classList.remove('active'));
            document.getElementById(`page-${page}`).classList.add('active');

            // Trigger page load
            if (page === 'accounts' && typeof loadAccounts === 'function') loadAccounts();
            if (page === 'downloads' && typeof loadDownloads === 'function') loadDownloads();
            if (page === 'analysis' && typeof loadAnalysis === 'function') loadAnalysis();
        });
    });

    // Settings modal
    const settingsBtn = document.getElementById('settings-btn');
    const modal = document.getElementById('settings-modal');
    const closeBtn = modal.querySelector('.modal-close');

    settingsBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        if (typeof loadSettings === 'function') loadSettings();
    });

    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });

    // Initial load
    if (typeof loadAccounts === 'function') loadAccounts();
});
