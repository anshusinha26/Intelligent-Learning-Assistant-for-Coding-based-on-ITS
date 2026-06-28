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
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast.js";
import { Link, useNavigate } from "react-router-dom";
import { apiRequest } from "@/lib/api.js";

function ForgotPassword() {
    const [email, setEmail] = useState("demo@example.com");
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();
    const navigate = useNavigate();

    const submit = async () => {
        setLoading(true);
        try {
            const data = await apiRequest("/auth/forgot-password", {
                method: "POST",
                body: { email },
            });
            if (data.dev_otp) {
                toast({
                    title: "OTP generated",
                    description: `Dev OTP: ${data.dev_otp}`,
                });
            } else {
                toast({
                    title: "OTP generated",
                    description: data.message,
                });
            }
            navigate("/verify-otp", {
                state: {
                    email,
                    purpose: "password_reset",
                },
            });
        } catch (error) {
            toast({
                title: "Request failed",
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
                        submit();
                    }}
                >
                    <CardHeader>
                        <CardTitle>Forgot password</CardTitle>
                        <CardDescription>
                            Enter your account email to generate an OTP.
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
                                    placeholder="you@example.com"
                                />
                            </div>
                            <Button variant="link" asChild className="px-0">
                                <Link to="/login">Back to login</Link>
                            </Button>
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-end">
                        <Button disabled={loading}>
                            {loading ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : null}
                            Send OTP
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}

export default ForgotPassword;
