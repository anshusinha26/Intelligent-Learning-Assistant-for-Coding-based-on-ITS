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
import {
    InputOTP,
    InputOTPGroup,
    InputOTPSlot,
} from "@/components/ui/input-otp.jsx";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast.js";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { apiRequest } from "@/lib/api.js";

function VerifyOtp() {
    const { state } = useLocation();
    const navigate = useNavigate();
    const { toast } = useToast();
    const email = state?.email || "";
    const purpose = state?.purpose || "password_reset";
    const [otp, setOtp] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!email) {
            navigate("/forgot-password");
        }
    }, [email, navigate]);

    const submit = async () => {
        if (!email || otp.length !== 6) {
            return;
        }
        setLoading(true);
        try {
            const data = await apiRequest("/auth/verify-otp", {
                method: "POST",
                body: { email, otp, purpose },
            });
            toast({
                title: "OTP verified",
                description: data.message,
            });
            if (data.reset_token) {
                navigate("/reset-password", {
                    state: { resetToken: data.reset_token },
                });
            } else {
                navigate("/login");
            }
        } catch (error) {
            toast({
                title: "OTP verification failed",
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
                        <CardTitle>Verify OTP</CardTitle>
                        <CardDescription>
                            Enter the 6-digit OTP for {email}.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div className="space-y-2">
                            <Label htmlFor="otp">One-Time Password</Label>
                            <div className="flex justify-center">
                                <InputOTP
                                    id="otp"
                                    maxLength={6}
                                    value={otp}
                                    onChange={(value) => setOtp(value)}
                                >
                                    <InputOTPGroup>
                                        <InputOTPSlot index={0} />
                                        <InputOTPSlot index={1} />
                                        <InputOTPSlot index={2} />
                                        <InputOTPSlot index={3} />
                                        <InputOTPSlot index={4} />
                                        <InputOTPSlot index={5} />
                                    </InputOTPGroup>
                                </InputOTP>
                            </div>
                        </div>
                        <Button variant="link" asChild className="px-0">
                            <Link to="/forgot-password">Resend OTP</Link>
                        </Button>
                    </CardContent>
                    <CardFooter className="flex justify-end">
                        <Button disabled={loading || otp.length !== 6}>
                            {loading ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : null}
                            Verify
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}

export default VerifyOtp;
