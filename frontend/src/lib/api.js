const DEFAULT_API_URL = "http://localhost:8001/api";

function ensureApiPath(urlObject) {
    const pathname = urlObject.pathname.replace(/\/+$/, "");
    if (!pathname || pathname === "/") {
        urlObject.pathname = "/api";
        return true;
    }
    if (pathname === "/api") {
        urlObject.pathname = "/api";
        return true;
    }
    if (pathname.endsWith("/api")) {
        urlObject.pathname = pathname;
        return true;
    }
    return false;
}

function normalizeApiBaseUrl(value) {
    if (!value || typeof value !== "string") {
        return null;
    }
    try {
        const parsed = new URL(value.trim());
        if (!ensureApiPath(parsed)) {
            return null;
        }
        parsed.hash = "";
        parsed.search = "";
        return parsed.toString().replace(/\/$/, "");
    } catch {
        return null;
    }
}

function resolveFallbackApiUrl() {
    const fallback =
        import.meta.env?.VITE_API_URL ||
        import.meta.env?.REACT_APP_SERVER_URL ||
        DEFAULT_API_URL;
    return normalizeApiBaseUrl(fallback) || DEFAULT_API_URL;
}

function buildApiUrl(baseUrl, path) {
    const base = normalizeApiBaseUrl(baseUrl) || resolveFallbackApiUrl();
    const normalizedPath = String(path || "")
        .replace(/^\/+/, "");
    return new URL(normalizedPath, `${base}/`).toString();
}

export function getApiUrl() {
    const fallback = resolveFallbackApiUrl();
    const override = new URLSearchParams(window.location.search).get("api");
    if (override) {
        const normalized = normalizeApiBaseUrl(override) || fallback;
        localStorage.setItem("apiUrl", normalized);
        return normalized;
    }
    const stored = localStorage.getItem("apiUrl");
    if (stored) {
        const normalized = normalizeApiBaseUrl(stored);
        if (normalized) {
            if (normalized !== stored) {
                localStorage.setItem("apiUrl", normalized);
            }
            return normalized;
        }
        localStorage.removeItem("apiUrl");
    }
    return fallback;
}

function readStoredUser() {
    try {
        const raw = localStorage.getItem("user");
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

async function parseJsonSafe(response) {
    return response.json().catch(() => ({}));
}

function extractApiError(data) {
    if (!data || typeof data !== "object") {
        return "Request failed";
    }
    if (data.error && typeof data.error === "object") {
        return data.error.message || data.error.code || "Request failed";
    }
    return data.detail || data.message || "Request failed";
}

export async function apiRequest(path, { token, method = "GET", body } = {}) {
    const apiBase = getApiUrl();
    const request = async (activeToken) => {
        const headers = {
            "Content-Type": "application/json",
        };
        if (activeToken) {
            headers.Authorization = `Bearer ${activeToken}`;
        }
        const endpoint = buildApiUrl(apiBase, path);
        return fetch(endpoint, {
            method,
            headers,
            body: body == null ? undefined : JSON.stringify(body),
        });
    };

    let response = await request(token);
    if (response.status === 401 && token) {
        const storedUser = readStoredUser();
        const refreshToken = storedUser?.refreshToken;
        if (refreshToken) {
            const refreshResponse = await fetch(
                buildApiUrl(apiBase, "/auth/refresh"),
                {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: refreshToken }),
                },
            );
            const refreshData = await parseJsonSafe(refreshResponse);
            if (refreshResponse.ok && refreshData.access_token) {
                const updatedUser = {
                    ...(storedUser || {}),
                    token: refreshData.access_token,
                    refreshToken: refreshData.refresh_token || refreshToken,
                    id: refreshData.user_id ?? storedUser?.id ?? null,
                    name: refreshData.name ?? storedUser?.name ?? null,
                    email: refreshData.email ?? storedUser?.email ?? null,
                    isAuthenticated: true,
                };
                localStorage.setItem("user", JSON.stringify(updatedUser));
                response = await request(updatedUser.token);
            } else {
                localStorage.removeItem("user");
            }
        }
    }

    const data = await parseJsonSafe(response);
    if (!response.ok) {
        const error = new Error(extractApiError(data));
        error.status = response.status;
        error.endpoint = buildApiUrl(apiBase, path);
        throw error;
    }
    return data;
}

export function normalizeProblem(problem) {
    return {
        ...problem,
        id: problem.problem_id,
        solved: false,
    };
}
