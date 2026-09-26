/**
 * Scanner module
 * Embeds the Folder Scanner table served by the unified Propack server.
 */

(function () {
    const SCANNER_URL = '/scanner/?embed=1';

    function getScannerUrl(extraParams) {
        const url = new URL(SCANNER_URL, window.location.origin);
        try {
            const rawUser = localStorage.getItem('current_user') || sessionStorage.getItem('current_user') || '{}';
            const user = JSON.parse(rawUser);
            const userId = user.user_id || user.id || '';
            const username = user.username || '';
            if (userId) url.searchParams.set('user_id', userId);
            if (username) url.searchParams.set('username', username);
        } catch (error) {
            // Keep scanner usable when the stored profile cannot be parsed.
        }
        Object.entries(extraParams || {}).forEach(([key, value]) => {
            url.searchParams.set(key, value);
        });
        return url.pathname + url.search;
    }

    function scannerText(key, fallback) {
        if (typeof t === 'function') {
            const translated = t(key);
            if (translated && translated !== key) return translated;
        }
        return fallback;
    }

    function renderScannerModule() {
        const container = document.getElementById('scanner-container');
        if (!container) return;
        const scannerUrl = getScannerUrl();

        container.innerHTML = `
            <div class="scanner-embed-shell">
                <div class="scanner-embed-toolbar">
                    <button type="button" class="scanner-embed-title" id="scanner-open-settings">
                        <i class="bi bi-folder-symlink"></i>
                        <span data-i18n="scanner_title">${scannerText('scanner_title', 'Cài đặt quét')}</span>
                    </button>
                    <div class="scanner-embed-actions">
                        <button type="button" class="btn btn-outline-secondary btn-sm" id="scanner-refresh-frame">
                            <i class="bi bi-arrow-clockwise"></i>
                            <span data-i18n="refresh">Refresh</span>
                        </button>
                    </div>
                </div>
                <div class="scanner-frame-wrap">
                    <div class="scanner-frame-loading" id="scanner-frame-loading">
                        <div class="spinner-border text-primary" role="status"></div>
                        <span data-i18n="loading_scanner">${scannerText('loading_scanner', 'Đang tải cài đặt quét...')}</span>
                    </div>
                    <iframe
                        id="scanner-frame"
                        class="scanner-frame"
                        src="${scannerUrl}"
                        title="${scannerText('scanner_title', 'Cài đặt quét')}"
                        loading="lazy"
                    ></iframe>
                </div>
            </div>
        `;

        if (typeof translatePage === 'function') {
            translatePage();
        }

        const frame = document.getElementById('scanner-frame');
        const loading = document.getElementById('scanner-frame-loading');
        const refresh = document.getElementById('scanner-refresh-frame');
        const settings = document.getElementById('scanner-open-settings');

        if (frame && loading) {
            frame.addEventListener('load', () => {
                loading.style.display = 'none';
            });
        }

        if (refresh && frame) {
            refresh.addEventListener('click', () => {
                if (loading) loading.style.display = 'flex';
                frame.src = getScannerUrl({ _: String(Date.now()) });
            });
        }

        if (settings && frame) {
            settings.addEventListener('click', () => {
                frame.contentWindow?.postMessage({ type: 'scanner:openSettings' }, window.location.origin);
            });
        }
    }

    window.initScannerModule = function () {
        renderScannerModule();
    };

    window.onScannerTabInit = function () {
        const frame = document.getElementById('scanner-frame');
        if (frame && !frame.src) {
            frame.src = getScannerUrl();
        }
    };
})();
