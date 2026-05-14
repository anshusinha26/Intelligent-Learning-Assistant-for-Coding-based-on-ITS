import { ThemeProvider } from "@/components/theme-provider.jsx";
import {
    createBrowserRouter,
    redirect,
    RouterProvider,
} from "react-router-dom";
import Home from "@/pages/Home.jsx";
import Layout from "@/pages/Layout.jsx";
import Login from "@/pages/Login.jsx";
import Register from "@/pages/Register.jsx";
import Code from "@/pages/Code.jsx";
import Problems from "@/pages/Problems.jsx";
import AuthContext from "@/context/auth-provider.jsx";
import { useEffect, useMemo, useState } from "react";
import "@fontsource/bricolage-grotesque";
import "@fontsource/cascadia-code";
import Submissions from "@/pages/Submissions.jsx";
import Dashboard from "@/pages/Dashboard.jsx";
import NoPageFound from "@/pages/404.jsx";
import { apiRequest, normalizeProblem } from "@/lib/api.js";

const initialUser = {
    id: null,
    name: null,
    email: null,
    token: null,
    points: 0,
    isAuthenticated: false,
};

function buildDescription(problem) {
    const lines = [
        `# ${problem.title}`,
        "",
        problem.description || "Solve this curated DSA problem.",
        "",
        problem.examples ? `**Example**\n\n${problem.examples}` : "",
        problem.constraints ? `**Constraints**\n\n${problem.constraints}` : "",
        problem.source_url ? `[Open original problem](${problem.source_url})` : "",
    ];
    return lines.filter(Boolean).join("\n\n");
}

function parseTestCases(problem) {
    try {
        const cases = JSON.parse(problem.test_cases || "[]");
        return cases.map((testCase, index) => ({
            id: index + 1,
            input: JSON.stringify(testCase.input),
            output: JSON.stringify(testCase.expected),
        }));
    } catch {
        return [];
    }
}

function App() {
    const [user, setUserState] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem("user")) || initialUser;
        } catch {
            return initialUser;
        }
    });

    const setUser = (nextUser) => {
        setUserState(nextUser);
        localStorage.setItem("user", JSON.stringify(nextUser));
    };

    useEffect(() => {
        if (!user.isAuthenticated) {
            return;
        }
        apiRequest("/auth/me", { token: user.token })
            .then((me) => {
                setUser({
                    ...user,
                    id: me.user_id,
                    name: me.name,
                    email: me.email,
                });
            })
            .catch(() => setUser(initialUser));
    }, []);

    const router = useMemo(
        () =>
            createBrowserRouter([
                {
                    element: <Layout />,
                    errorElement: (
                        <p className="w-screen h-full-w-nav flex justify-center align-middle items-center">
                            Something went wrong
                        </p>
                    ),
                    children: [
                        { path: "/", element: <Home /> },
                        {
                            path: "/login",
                            loader: ({ request }) => {
                                const searchParams = new URL(
                                    request.url,
                                ).searchParams;
                                if (user.isAuthenticated) {
                                    return redirect(
                                        searchParams.get("next") || "/",
                                    );
                                }
                                return null;
                            },
                            element: <Login />,
                        },
                        {
                            path: "/register",
                            loader: () =>
                                user.isAuthenticated ? redirect("/") : null,
                            element: <Register />,
                        },
                        {
                            path: "/problems",
                            loader: async () => {
                                if (!user.isAuthenticated) {
                                    return redirect("/login?next=/problems");
                                }
                                const problems = await apiRequest(
                                    "/problems?limit=700",
                                    { token: user.token },
                                );
                                return problems.map(normalizeProblem);
                            },
                            element: <Problems />,
                        },
                        {
                            path: "/problem/:id",
                            loader: async ({ params: { id } }) => {
                                if (!user.isAuthenticated) {
                                    return redirect(`/login?next=/problem/${id}`);
                                }
                                const problem = await apiRequest(
                                    `/problems/${encodeURIComponent(id)}`,
                                    { token: user.token },
                                );
                                return {
                                    ...normalizeProblem(problem),
                                    description: buildDescription(problem),
                                    starterCode: [
                                        {
                                            language: "python",
                                            code:
                                                problem.starter_code ||
                                                "def solve(*args):\n    return None\n",
                                        },
                                    ],
                                    testCase: parseTestCases(problem),
                                };
                            },
                            element: <Code />,
                        },
                        {
                            path: "/dashboard",
                            loader: async () => {
                                if (!user.isAuthenticated) {
                                    return redirect("/login?next=/dashboard");
                                }
                                const [dashboard, weaknesses, revisions] =
                                    await Promise.all([
                                        apiRequest("/analytics/dashboard", {
                                            token: user.token,
                                        }),
                                        apiRequest("/analytics/weaknesses", {
                                            token: user.token,
                                        }),
                                        apiRequest("/revisions/due", {
                                            token: user.token,
                                        }),
                                    ]);
                                return { dashboard, weaknesses, revisions };
                            },
                            element: <Dashboard />,
                        },
                        {
                            path: "/submissions",
                            loader: async () => {
                                if (!user.isAuthenticated) {
                                    return redirect("/login?next=/submissions");
                                }
                                const data = await apiRequest(
                                    "/submissions?limit=50",
                                    { token: user.token },
                                );
                                return { submissions: data.submissions, page: 1 };
                            },
                            element: <Submissions />,
                        },
                        { path: "*", element: <NoPageFound /> },
                    ],
                },
            ]),
        [user],
    );

    return (
        <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
            <AuthContext.Provider value={{ user, setUser }}>
                <RouterProvider router={router} />
            </AuthContext.Provider>
        </ThemeProvider>
    );
}

export default App;
