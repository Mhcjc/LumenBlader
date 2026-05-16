const API = {
    async get(url) {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`GET ${url}: ${resp.status}`);
        return resp.json();
    },

    async post(url, data) {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!resp.ok) throw new Error(`POST ${url}: ${resp.status}`);
        return resp.json();
    },

    async patch(url, data) {
        const resp = await fetch(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!resp.ok) throw new Error(`PATCH ${url}: ${resp.status}`);
        return resp.json();
    },

    async del(url) {
        const resp = await fetch(url, { method: 'DELETE' });
        if (!resp.ok) throw new Error(`DELETE ${url}: ${resp.status}`);
        return resp.json();
    },
};
