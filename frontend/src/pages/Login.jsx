import { useContext, useState } from "react";
import { Button } from "@/components/ui/button.jsx";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card.jsx";
import { Input } from "@/components/ui/input.jsx";
import { Label } from "@/components/ui/label.jsx";
import { PasswordInput } from "@/components/ui/password-input.jsx";
import { Loader2 } from "lucide-react";
import AuthContext from "@/context/auth-provider.jsx";
import { useToast } from "@/hooks/use-toast.js";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { apiRequest } from "@/lib/api.js";

function Login() {
    const [email, setEmail] = useState("demo@example.com");
    const [password, setPassword] = useState("demo123");
    const [loading, setLoading] = useState(false);
    const { setUser } = useContext(AuthContext);
    const { toast } = useToast();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const login = async () => {
        setLoading(true);
        try {
            const data = await apiRequest("/auth/login", {
                method: "POST",
                body: { email, password },
            });
            setUser({
                id: data.user_id,
                name: data.name,
                email: data.email,
                token: data.access_token,
                refreshToken: data.refresh_token || null,
                points: 0,
                isAuthenticated: true,
            });
            toast({ title: "Success", description: "Logged in" });
            const nextParam = searchParams.get("next");
            const safeNext =
                typeof nextParam === "string" &&
                nextParam.startsWith("/") &&
                !nextParam.startsWith("//")
                    ? nextParam
                    : "/problems";
            navigate(safeNext);
        } catch (error) {
            toast({
                title: "Couldn't log in",
                description: error.message,
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-full-w-nav w-full bg-[linear-gradient(135deg,hsl(var(--background))_0%,hsl(var(--secondary))_100%)] px-4 py-10 flex items-center justify-center">
            <Card className="w-full max-w-[390px] shadow-lg">
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        login();
                    }}
                >
                    <CardHeader>
                        <CardTitle>Welcome back</CardTitle>
                        <CardDescription>
                            Continue to your ILA Coding workspace
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid w-full items-center gap-4">
                            <div className="flex flex-col space-y-1.5">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    value={email}
                                    onChange={(event) =>
                                        setEmail(event.target.value)
                                    }
                                    placeholder="Your email"
                                />
                            </div>
                            <div className="flex flex-col space-y-1.5">
                                <Label htmlFor="password">Password</Label>
                                <PasswordInput
                                    id="password"
                                    value={password}
                                    onChange={(event) =>
                                        setPassword(event.target.value)
                                    }
                                    placeholder="Your password"
                                />
                            </div>
                            <Button variant="link" asChild className="px-0">
                                <Link to="/register">Create new account</Link>
                            </Button>
                            <Button variant="link" asChild className="px-0 w-max">
                                <Link to="/forgot-password">Forgot password?</Link>
                            </Button>
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-end">
                        <Button disabled={loading}>
                            {loading ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : null}
                            Log In
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}

export default Login;
