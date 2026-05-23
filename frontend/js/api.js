const API = {
    _timeout: 30000,

    async _fetch(url, options = {}) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this._timeout);
        try {
            return await fetch(url, { ...options, signal: controller.signal });
        } catch (e) {
            if (e.name === 'AbortError') throw new Error('请求超时，请检查 TikTokDownloader 服务是否正常');
            throw e;
        } finally {
            clearTimeout(timer);
        }
    },

    async get(url) {
        const resp = await this._fetch(url);
        if (!resp.ok) {
            const text = await resp.text().catch(() => '');
            let msg = text;
            try { msg = JSON.parse(text).detail || text; } catch {}
            throw new Error(msg || `GET ${url}: ${resp.status}`);
        }
        return resp.json();
    },

    async post(url, data) {
        const resp = await this._fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!resp.ok) {
            const text = await resp.text().catch(() => '');
            let msg = text;
            try { msg = JSON.parse(text).detail || text; } catch {}
            throw new Error(msg || `POST ${url}: ${resp.status}`);
        }
        return resp.json();
    },

    async patch(url, data) {
        const resp = await this._fetch(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!resp.ok) {
            const text = await resp.text().catch(() => '');
            let msg = text;
            try { msg = JSON.parse(text).detail || text; } catch {}
            throw new Error(msg || `PATCH ${url}: ${resp.status}`);
        }
        return resp.json();
    },

    async del(url) {
        const resp = await this._fetch(url, { method: 'DELETE' });
        if (!resp.ok) {
            const text = await resp.text().catch(() => '');
            let msg = text;
            try { msg = JSON.parse(text).detail || text; } catch {}
            throw new Error(msg || `DELETE ${url}: ${resp.status}`);
        }
        return resp.json();
    },
};
