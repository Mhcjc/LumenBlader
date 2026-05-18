const API = {
    async get(url) {
        const resp = await fetch(url);
        if (!resp.ok) {
            const text = await resp.text().catch(() => '');
            let msg = text;
            try { msg = JSON.parse(text).detail || text; } catch {}
            throw new Error(msg || `GET ${url}: ${resp.status}`);
        }
        return resp.json();
    },

    async post(url, data) {
        const resp = await fetch(url, {
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
        const resp = await fetch(url, {
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
        const resp = await fetch(url, { method: 'DELETE' });
        if (!resp.ok) {
            const text = await resp.text().catch(() => '');
            let msg = text;
            try { msg = JSON.parse(text).detail || text; } catch {}
            throw new Error(msg || `DELETE ${url}: ${resp.status}`);
        }
        return resp.json();
    },
};
