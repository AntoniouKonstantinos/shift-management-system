const API_BASE = "/api";

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    if (response.status === 204) return null;

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || `Request failed with status ${response.status}`);
    }

    return data;
}

const api = {
    get: (path) => apiRequest(path),
    post: (path, body) => apiRequest(path, { method: "POST", body: JSON.stringify(body) }),
    put: (path, body) => apiRequest(path, { method: "PUT", body: JSON.stringify(body) }),
    patch: (path, body) => apiRequest(path, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (path) => apiRequest(path, { method: "DELETE" }),
};