import { useContext, useState } from "react";
import { useLoaderData } from "react-router-dom";
import { Button } from "@/components/ui/button.jsx";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.jsx";
import { Input } from "@/components/ui/input.jsx";
import { Label } from "@/components/ui/label.jsx";
import { Textarea } from "@/components/ui/textarea.jsx";
import { useToast } from "@/hooks/use-toast.js";
import { Loader2 } from "lucide-react";
import AuthContext from "@/context/auth-provider.jsx";
import { apiRequest } from "@/lib/api.js";

function Notes() {
    const data = useLoaderData();
    const { user } = useContext(AuthContext);
    const { toast } = useToast();
    const [notes, setNotes] = useState(data.notes || []);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(false);
    const [createLoading, setCreateLoading] = useState(false);
    const [editingNoteId, setEditingNoteId] = useState(null);
    const [form, setForm] = useState({
        title: "",
        content: "",
        problem_id: "",
        pinned: false,
    });
    const [editForm, setEditForm] = useState({
        title: "",
        content: "",
        problem_id: "",
        pinned: false,
    });

    const loadNotes = async (query = "") => {
        setLoading(true);
        try {
            const params = new URLSearchParams({ limit: "200" });
            if (query.trim()) {
                params.set("q", query.trim());
            }
            const next = await apiRequest(`/notes?${params.toString()}`, {
                token: user.token,
            });
            setNotes(next.notes || []);
        } catch (error) {
            toast({ title: "Load failed", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const createNote = async () => {
        setCreateLoading(true);
        try {
            const created = await apiRequest("/notes", {
                token: user.token,
                method: "POST",
                body: {
                    title: form.title,
                    content: form.content,
                    problem_id: form.problem_id.trim() || null,
                    pinned: form.pinned,
                },
            });
            setNotes((prev) => [created, ...prev]);
            setForm({ title: "", content: "", problem_id: "", pinned: false });
            toast({ title: "Note created", description: "Saved successfully" });
        } catch (error) {
            toast({ title: "Create failed", description: error.message });
        } finally {
            setCreateLoading(false);
        }
    };

    const deleteNote = async (noteId) => {
        try {
            await apiRequest(`/notes/${noteId}`, {
                token: user.token,
                method: "DELETE",
            });
            setNotes((prev) => prev.filter((note) => note.note_id !== noteId));
            toast({ title: "Deleted", description: "Note removed" });
        } catch (error) {
            toast({ title: "Delete failed", description: error.message });
        }
    };

    const startEdit = (note) => {
        setEditingNoteId(note.note_id);
        setEditForm({
            title: note.title,
            content: note.content,
            problem_id: note.problem_id || "",
            pinned: Boolean(note.pinned),
        });
    };

    const saveEdit = async () => {
        if (!editingNoteId) {
            return;
        }
        try {
            const updated = await apiRequest(`/notes/${editingNoteId}`, {
                token: user.token,
                method: "PUT",
                body: {
                    title: editForm.title,
                    content: editForm.content,
                    problem_id: editForm.problem_id.trim() || null,
                    pinned: editForm.pinned,
                },
            });
            setNotes((prev) =>
                prev.map((note) =>
                    note.note_id === editingNoteId ? updated : note,
                ),
            );
            setEditingNoteId(null);
            toast({ title: "Updated", description: "Note saved" });
        } catch (error) {
            toast({ title: "Update failed", description: error.message });
        }
    };

    return (
        <div className="min-h-full-w-nav w-full bg-background px-4 py-8 md:px-6">
            <div className="mx-auto grid max-w-6xl gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Notes</CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-3">
                        <div className="grid gap-2">
                            <Label htmlFor="title">Title</Label>
                            <Input
                                id="title"
                                value={form.title}
                                onChange={(event) =>
                                    setForm((prev) => ({
                                        ...prev,
                                        title: event.target.value,
                                    }))
                                }
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="problem_id">Problem ID (optional)</Label>
                            <Input
                                id="problem_id"
                                value={form.problem_id}
                                onChange={(event) =>
                                    setForm((prev) => ({
                                        ...prev,
                                        problem_id: event.target.value,
                                    }))
                                }
                                placeholder="two-sum"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="content">Content</Label>
                            <Textarea
                                id="content"
                                rows={4}
                                value={form.content}
                                onChange={(event) =>
                                    setForm((prev) => ({
                                        ...prev,
                                        content: event.target.value,
                                    }))
                                }
                            />
                        </div>
                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={form.pinned}
                                onChange={(event) =>
                                    setForm((prev) => ({
                                        ...prev,
                                        pinned: event.target.checked,
                                    }))
                                }
                            />
                            Pin note
                        </label>
                        <div className="flex justify-end">
                            <Button
                                disabled={
                                    createLoading ||
                                    form.title.trim().length === 0 ||
                                    form.content.trim().length === 0
                                }
                                onClick={createNote}
                            >
                                {createLoading ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : null}
                                Create Note
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>My Notes</CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-4">
                        <div className="flex gap-2">
                            <Input
                                placeholder="Search in title/content"
                                value={search}
                                onChange={(event) => setSearch(event.target.value)}
                            />
                            <Button
                                variant="outline"
                                onClick={() => loadNotes(search)}
                                disabled={loading}
                            >
                                {loading ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : null}
                                Search
                            </Button>
                        </div>
                        {notes.length === 0 ? (
                            <p className="text-sm text-muted-foreground">No notes yet.</p>
                        ) : (
                            notes.map((note) => (
                                <div
                                    key={note.note_id}
                                    className="rounded-md border border-border p-3"
                                >
                                    {editingNoteId === note.note_id ? (
                                        <div className="grid gap-2">
                                            <Input
                                                value={editForm.title}
                                                onChange={(event) =>
                                                    setEditForm((prev) => ({
                                                        ...prev,
                                                        title: event.target.value,
                                                    }))
                                                }
                                            />
                                            <Input
                                                value={editForm.problem_id}
                                                onChange={(event) =>
                                                    setEditForm((prev) => ({
                                                        ...prev,
                                                        problem_id: event.target.value,
                                                    }))
                                                }
                                                placeholder="problem id"
                                            />
                                            <Textarea
                                                rows={4}
                                                value={editForm.content}
                                                onChange={(event) =>
                                                    setEditForm((prev) => ({
                                                        ...prev,
                                                        content: event.target.value,
                                                    }))
                                                }
                                            />
                                            <label className="flex items-center gap-2 text-sm">
                                                <input
                                                    type="checkbox"
                                                    checked={editForm.pinned}
                                                    onChange={(event) =>
                                                        setEditForm((prev) => ({
                                                            ...prev,
                                                            pinned: event.target.checked,
                                                        }))
                                                    }
                                                />
                                                Pin note
                                            </label>
                                            <div className="flex gap-2 justify-end">
                                                <Button variant="outline" onClick={() => setEditingNoteId(null)}>
                                                    Cancel
                                                </Button>
                                                <Button onClick={saveEdit}>Save</Button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="grid gap-2">
                                            <div className="flex items-center justify-between gap-2">
                                                <h3 className="font-semibold">{note.title}</h3>
                                                <div className="flex gap-2">
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => startEdit(note)}
                                                    >
                                                        Edit
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => deleteNote(note.note_id)}
                                                    >
                                                        Delete
                                                    </Button>
                                                </div>
                                            </div>
                                            {note.problem_id ? (
                                                <p className="text-xs text-muted-foreground">
                                                    Problem: {note.problem_id}
                                                </p>
                                            ) : null}
                                            {note.pinned ? (
                                                <p className="text-xs text-primary">Pinned</p>
                                            ) : null}
                                            <p className="text-sm whitespace-pre-wrap">
                                                {note.content}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

export default Notes;
