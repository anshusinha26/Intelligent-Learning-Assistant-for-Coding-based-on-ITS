import { useContext, useEffect, useState } from "react";
import { useLoaderData, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.jsx";
import { Input } from "@/components/ui/input.jsx";
import { Label } from "@/components/ui/label.jsx";
import { PasswordInput } from "@/components/ui/password-input.jsx";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select.jsx";
import { useToast } from "@/hooks/use-toast.js";
import { Loader2 } from "lucide-react";
import AuthContext from "@/context/auth-provider.jsx";
import { apiRequest } from "@/lib/api.js";

function Settings() {
    const loaderData = useLoaderData();
    const [searchParams] = useSearchParams();
    const { user } = useContext(AuthContext);
    const { toast } = useToast();
    const [savingPreferences, setSavingPreferences] = useState(false);
    const [changingPassword, setChangingPassword] = useState(false);
    const [requestingOtp, setRequestingOtp] = useState(false);
    const [verifyingOtp, setVerifyingOtp] = useState(false);
    const [profile, setProfile] = useState({ email_verified: false });
    const [verificationOtp, setVerificationOtp] = useState("");
    const [settings, setSettings] = useState({
        theme: loaderData.theme || "light",
        editor_language: loaderData.editor_language || "python",
        email_notifications: Boolean(loaderData.email_notifications),
        ai_assistant_enabled: Boolean(loaderData.ai_assistant_enabled),
        daily_goal: loaderData.daily_goal || 2,
    });
    const [passwordForm, setPasswordForm] = useState({
        current_password: "",
        new_password: "",
    });

    useEffect(() => {
        apiRequest("/auth/me", { token: user.token })
            .then((data) => setProfile(data))
            .catch(() => null);
    }, [user.token]);

    const savePreferences = async () => {
        setSavingPreferences(true);
        try {
            const updated = await apiRequest("/settings", {
                token: user.token,
                method: "PUT",
                body: settings,
            });
            setSettings({
                theme: updated.theme,
                editor_language: updated.editor_language,
                email_notifications: Boolean(updated.email_notifications),
                ai_assistant_enabled: Boolean(updated.ai_assistant_enabled),
                daily_goal: updated.daily_goal,
            });
            toast({ title: "Saved", description: "Preferences updated" });
        } catch (error) {
            toast({ title: "Save failed", description: error.message });
        } finally {
            setSavingPreferences(false);
        }
    };

    const changePassword = async () => {
        setChangingPassword(true);
        try {
            await apiRequest("/auth/change-password", {
                token: user.token,
                method: "POST",
                body: passwordForm,
            });
            setPasswordForm({ current_password: "", new_password: "" });
            toast({
                title: "Password changed",
                description: "Use your new password from next login.",
            });
        } catch (error) {
            toast({
                title: "Password change failed",
                description: error.message,
            });
        } finally {
            setChangingPassword(false);
        }
    };

    const requestVerificationOtp = async () => {
        setRequestingOtp(true);
        try {
            const data = await apiRequest("/auth/email-verification/request", {
                token: user.token,
                method: "POST",
            });
            toast({
                title: "Verification OTP",
                description: data.dev_otp
                    ? `Dev OTP: ${data.dev_otp}`
                    : data.message,
            });
        } catch (error) {
            toast({
                title: "OTP request failed",
                description: error.message,
            });
        } finally {
            setRequestingOtp(false);
        }
    };

    const verifyEmailOtp = async () => {
        setVerifyingOtp(true);
        try {
            await apiRequest("/auth/email-verification/verify", {
                token: user.token,
                method: "POST",
                body: { otp: verificationOtp },
            });
            setVerificationOtp("");
            const me = await apiRequest("/auth/me", { token: user.token });
            setProfile(me);
            toast({
                title: "Email verified",
                description: "Verification completed.",
            });
        } catch (error) {
            toast({
                title: "Verification failed",
                description: error.message,
            });
        } finally {
            setVerifyingOtp(false);
        }
    };

    const securityMode = searchParams.get("tab") === "security";

    return (
        <div className="min-h-full-w-nav w-full bg-background px-4 py-8 md:px-6">
            <div className="mx-auto grid max-w-5xl gap-6">
                <Card className={securityMode ? "order-2" : "order-1"}>
                    <CardHeader>
                        <CardTitle>Preferences</CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-4">
                        <div className="grid gap-2">
                            <Label>Theme</Label>
                            <Select
                                value={settings.theme}
                                onValueChange={(value) =>
                                    setSettings((prev) => ({
                                        ...prev,
                                        theme: value,
                                    }))
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Theme" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="light">Light</SelectItem>
                                    <SelectItem value="dark">Dark</SelectItem>
                                    <SelectItem value="system">System</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-2">
                            <Label>Editor Language</Label>
                            <Select
                                value={settings.editor_language}
                                onValueChange={(value) =>
                                    setSettings((prev) => ({
                                        ...prev,
                                        editor_language: value,
                                    }))
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Language" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="python">Python</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="daily_goal">Daily Goal</Label>
                            <Input
                                id="daily_goal"
                                type="number"
                                min={1}
                                max={50}
                                value={settings.daily_goal}
                                onChange={(event) =>
                                    setSettings((prev) => ({
                                        ...prev,
                                        daily_goal: Number(event.target.value || 1),
                                    }))
                                }
                            />
                        </div>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.email_notifications}
                                onChange={(event) =>
                                    setSettings((prev) => ({
                                        ...prev,
                                        email_notifications: event.target.checked,
                                    }))
                                }
                            />
                            Email notifications
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={settings.ai_assistant_enabled}
                                onChange={(event) =>
                                    setSettings((prev) => ({
                                        ...prev,
                                        ai_assistant_enabled: event.target.checked,
                                    }))
                                }
                            />
                            AI assistant enabled
                        </label>
                        <div className="flex justify-end">
                            <Button onClick={savePreferences} disabled={savingPreferences}>
                                {savingPreferences ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : null}
                                Save Preferences
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card className={securityMode ? "order-1" : "order-2"}>
                    <CardHeader>
                        <CardTitle>Security</CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-5">
                        <div className="grid gap-2">
                            <Label>Email verification</Label>
                            <p className="text-sm text-muted-foreground">
                                Status: {profile.email_verified ? "Verified" : "Not Verified"}
                            </p>
                            {!profile.email_verified ? (
                                <div className="flex flex-col gap-2">
                                    <div>
                                        <Button
                                            type="button"
                                            variant="outline"
                                            disabled={requestingOtp}
                                            onClick={requestVerificationOtp}
                                        >
                                            {requestingOtp ? (
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            ) : null}
                                            Generate OTP
                                        </Button>
                                    </div>
                                    <div className="flex gap-2">
                                        <Input
                                            value={verificationOtp}
                                            onChange={(event) =>
                                                setVerificationOtp(event.target.value)
                                            }
                                            placeholder="Enter OTP"
                                        />
                                        <Button
                                            type="button"
                                            onClick={verifyEmailOtp}
                                            disabled={verifyingOtp || verificationOtp.length < 4}
                                        >
                                            {verifyingOtp ? (
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            ) : null}
                                            Verify
                                        </Button>
                                    </div>
                                </div>
                            ) : null}
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="current_password">Current Password</Label>
                            <PasswordInput
                                id="current_password"
                                value={passwordForm.current_password}
                                onChange={(event) =>
                                    setPasswordForm((prev) => ({
                                        ...prev,
                                        current_password: event.target.value,
                                    }))
                                }
                            />
                            <Label htmlFor="new_password">New Password</Label>
                            <PasswordInput
                                id="new_password"
                                value={passwordForm.new_password}
                                onChange={(event) =>
                                    setPasswordForm((prev) => ({
                                        ...prev,
                                        new_password: event.target.value,
                                    }))
                                }
                            />
                            <div className="flex justify-end">
                                <Button
                                    type="button"
                                    disabled={
                                        changingPassword ||
                                        passwordForm.current_password.length === 0 ||
                                        passwordForm.new_password.length < 6
                                    }
                                    onClick={changePassword}
                                >
                                    {changingPassword ? (
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    ) : null}
                                    Change Password
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

export default Settings;
