import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button.jsx";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card.jsx";
import { Label } from "@/components/ui/label.jsx";
import { PasswordInput } from "@/components/ui/password-input.jsx";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast.js";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { apiRequest } from "@/lib/api.js";

function ResetPassword() {
    const { state } = useLocation();
    const navigate = useNavigate();
    const { toast } = useToast();
    const resetToken = state?.resetToken || "";
    const [newPassword, setNewPassword] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!resetToken) {
            navigate("/forgot-password");
        }
    }, [navigate, resetToken]);

    const submit = async () => {
        setLoading(true);
        try {
            await apiRequest("/auth/reset-password", {
                method: "POST",
                body: {
                    reset_token: resetToken,
                    new_password: newPassword,
                },
            });
            toast({
                title: "Password reset",
                description: "Your password was updated. Log in with the new password.",
            });
            navigate("/login");
        } catch (error) {
            toast({
                title: "Reset failed",
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
                        <CardTitle>Reset password</CardTitle>
                        <CardDescription>Enter your new password.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid w-full items-center gap-4">
                            <div className="flex flex-col space-y-1.5">
                                <Label htmlFor="newPassword">New Password</Label>
                                <PasswordInput
                                    id="newPassword"
                                    value={newPassword}
                                    onChange={(event) =>
                                        setNewPassword(event.target.value)
                                    }
                                    placeholder="At least 6 characters"
                                />
                            </div>
                            <Button variant="link" asChild className="px-0">
                                <Link to="/login">Back to login</Link>
                            </Button>
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-end">
                        <Button disabled={loading || newPassword.length < 6}>
                            {loading ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : null}
                            Reset Password
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}

export default ResetPassword;
