import { useState } from "react";
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
import { useToast } from "@/hooks/use-toast.js";
import { Link, useNavigate } from "react-router-dom";
import { apiRequest } from "@/lib/api.js";

function Register() {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();
    const navigate = useNavigate();

    const register = async () => {
        setLoading(true);
        try {
            await apiRequest("/auth/register", {
                method: "POST",
                body: {
                    name,
                    email,
                    password,
                    target_level: "medium",
                },
            });
            toast({
                title: "Success",
                description: "Account created. Log in to continue.",
            });
            navigate("/login");
        } catch (error) {
            toast({
                title: "Couldn't register",
                description: error.message,
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full-w-nav w-screen m-auto flex items-center justify-center">
            <Card className="w-[350px]">
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        register();
                    }}
                >
                    <CardHeader>
                        <CardTitle>Register</CardTitle>
                        <CardDescription>Register on code</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid w-full items-center gap-4">
                            <div className="flex flex-col space-y-1.5">
                                <Label htmlFor="name">Name</Label>
                                <Input
                                    id="name"
                                    value={name}
                                    onChange={(event) =>
                                        setName(event.target.value)
                                    }
                                    placeholder="Your name"
                                />
                            </div>
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
                                <Link to="/login">Already have an account?</Link>
                            </Button>
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-end">
                        <Button disabled={loading}>
                            {loading ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : null}
                            Register
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}

export default Register;
