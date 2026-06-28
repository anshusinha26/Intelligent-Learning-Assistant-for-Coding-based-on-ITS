import { useContext, useState } from "react";
import { useLoaderData, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.jsx";
import { Input } from "@/components/ui/input.jsx";
import { useToast } from "@/hooks/use-toast.js";
import { Loader2 } from "lucide-react";
import AuthContext from "@/context/auth-provider.jsx";
import { apiRequest } from "@/lib/api.js";

function Bookmarks() {
    const data = useLoaderData();
    const { user } = useContext(AuthContext);
    const { toast } = useToast();
    const navigate = useNavigate();
    const [bookmarks, setBookmarks] = useState(data.bookmarks || []);
    const [problemId, setProblemId] = useState("");
    const [saving, setSaving] = useState(false);

    const refreshBookmarks = async () => {
        const next = await apiRequest("/bookmarks?limit=200", {
            token: user.token,
        });
        setBookmarks(next.bookmarks || []);
    };

    const createBookmark = async () => {
        setSaving(true);
        try {
            await apiRequest("/bookmarks", {
                token: user.token,
                method: "POST",
                body: { problem_id: problemId.trim() },
            });
            setProblemId("");
            await refreshBookmarks();
            toast({ title: "Bookmarked", description: "Problem added to bookmarks." });
        } catch (error) {
            toast({ title: "Bookmark failed", description: error.message });
        } finally {
            setSaving(false);
        }
    };

    const removeBookmark = async (id) => {
        try {
            await apiRequest(`/bookmarks/${encodeURIComponent(id)}`, {
                token: user.token,
                method: "DELETE",
            });
            setBookmarks((prev) => prev.filter((item) => item.problem_id !== id));
            toast({ title: "Removed", description: "Bookmark removed." });
        } catch (error) {
            toast({ title: "Remove failed", description: error.message });
        }
    };

    return (
        <div className="min-h-full-w-nav w-full bg-background px-4 py-8 md:px-6">
            <div className="mx-auto grid max-w-5xl gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Add Bookmark</CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-3 sm:flex-row">
                        <Input
                            value={problemId}
                            onChange={(event) => setProblemId(event.target.value)}
                            placeholder="Problem ID, e.g. two-sum"
                        />
                        <Button
                            onClick={createBookmark}
                            disabled={saving || problemId.trim().length === 0}
                        >
                            {saving ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : null}
                            Add
                        </Button>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>My Bookmarks</CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-3">
                        {bookmarks.length === 0 ? (
                            <p className="text-sm text-muted-foreground">No bookmarks yet.</p>
                        ) : (
                            bookmarks.map((item) => (
                                <div
                                    key={item.bookmark_id}
                                    className="flex items-center justify-between gap-3 rounded-md border border-border p-3"
                                >
                                    <button
                                        type="button"
                                        className="text-left"
                                        onClick={() => navigate(`/problem/${item.problem_id}`)}
                                    >
                                        <p className="font-medium">{item.title || item.problem_id}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {item.problem_id}
                                            {item.topic ? ` · ${item.topic}` : ""}
                                            {item.difficulty ? ` · ${item.difficulty}` : ""}
                                        </p>
                                    </button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => removeBookmark(item.problem_id)}
                                    >
                                        Remove
                                    </Button>
                                </div>
                            ))
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

export default Bookmarks;
