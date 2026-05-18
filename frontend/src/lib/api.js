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

export async function apiRequest(path, { token, method = "GET", body } = {}) {
    const headers = {
        "Content-Type": "application/json",
    };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${getApiUrl()}${path}`, {
        method,
        headers,
        body: body == null ? undefined : JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));
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
