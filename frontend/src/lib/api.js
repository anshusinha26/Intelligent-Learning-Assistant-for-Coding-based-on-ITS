const DEFAULT_API_URL = "http://localhost:8001/api";
const STALE_API_URLS = new Set(["http://localhost:8020/api"]);

export function getApiUrl() {
    const override = new URLSearchParams(window.location.search).get("api");
    if (override) {
        localStorage.setItem("apiUrl", override);
        return override;
    }
    const stored = localStorage.getItem("apiUrl");
    if (stored && !STALE_API_URLS.has(stored)) {
        return stored;
    }
    if (stored) {
        localStorage.removeItem("apiUrl");
    }
    return (
        import.meta.env.VITE_API_URL ||
        import.meta.env.REACT_APP_SERVER_URL ||
        DEFAULT_API_URL
    );
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

export async function apiRequest(path, { token, method = "GET", body } = {}) {
    const request = async (activeToken) => {
        const headers = {
            "Content-Type": "application/json",
        };
        if (activeToken) {
            headers.Authorization = `Bearer ${activeToken}`;
        }
        return fetch(`${getApiUrl()}${path}`, {
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
            const refreshResponse = await fetch(`${getApiUrl()}/auth/refresh`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });
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
        throw new Error(data.detail || "Request failed");
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
