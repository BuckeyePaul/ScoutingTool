(function () {
    async function parseJsonSafe(response) {
        try {
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    async function getJson(url) {
        const response = await fetch(url);
        const data = await parseJsonSafe(response);
        return { response, data };
    }

    async function postJson(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {})
        });
        const data = await parseJsonSafe(response);
        return { response, data };
    }

    async function postNoBody(url) {
        const response = await fetch(url, { method: 'POST' });
        const data = await parseJsonSafe(response);
        return { response, data };
    }

    window.ApiClient = {
        getJson,
        postJson,
        postNoBody
    };
})();
