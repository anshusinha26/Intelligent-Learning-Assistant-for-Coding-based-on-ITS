const DEFAULT_API_URL = "http://localhost:8020/api";

export function getApiUrl() {
    const override = new URLSearchParams(window.location.search).get("api");
    if (override) {
        localStorage.setItem("apiUrl", override);
        return override;
    }
    return (
        localStorage.getItem("apiUrl") ||
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
