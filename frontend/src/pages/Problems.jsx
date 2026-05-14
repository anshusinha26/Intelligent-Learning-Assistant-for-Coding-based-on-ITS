import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table.jsx";
import { useLoaderData, useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge.jsx";
import { Check, LibraryBig } from "lucide-react";

function Problems() {
    const problemStatements = useLoaderData();
    const navigate = useNavigate();

    if (problemStatements == null) {
        return (
            <div className="flex h-full-w-nav w-screen items-center justify-center">
                An error occurred while fetching problem statements
            </div>
        );
    }

    const getDifficultyClass = (difficulty) => {
        if (difficulty === "Easy") {
            return "bg-emerald-100 text-emerald-800 hover:bg-emerald-100";
        }
        if (difficulty === "Medium") {
            return "bg-amber-100 text-amber-800 hover:bg-amber-100";
        }
        return "bg-rose-100 text-rose-800 hover:bg-rose-100";
    };

    return (
        <div className="min-h-full-w-nav w-full bg-background px-4 py-8 md:px-6">
            <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-normal text-primary">
                        <LibraryBig className="h-4 w-4" />
                        Adaptive practice bank
                    </div>
                    <h1 className="text-3xl font-bold tracking-normal text-foreground">
                        Choose a DSA problem
                    </h1>
                    <p className="max-w-3xl text-muted-foreground">
                        Solve freely from the curated bank. Each accepted,
                        wrong, or manual attempt feeds the learner model and
                        improves the next recommendation cycle.
                    </p>
                    <Badge variant="secondary" className="mt-2 w-max">
                        {problemStatements.length} problems available
                    </Badge>
                </div>

                <div className="overflow-hidden rounded-md border border-border bg-card shadow-sm">
                    <Table>
                        <TableHeader>
                            <TableRow className="bg-muted/50">
                                <TableHead>Problem</TableHead>
                                <TableHead className="w-28">
                                    Difficulty
                                </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {problemStatements.map((problemStatement) => (
                                <TableRow
                                    key={problemStatement.id}
                                    onClick={() =>
                                        navigate(
                                            `/problem/${problemStatement.id}`,
                                        )
                                    }
                                    className="group hover:cursor-pointer hover:bg-secondary/50"
                                >
                                    <TableCell className="flex w-full max-w-[90%] flex-row items-center gap-2 overflow-ellipsis font-medium decoration-primary underline-offset-2 group-hover:underline">
                                        {problemStatement.title}
                                        {problemStatement.solved ? (
                                            <Check className="text-primary" />
                                        ) : null}
                                    </TableCell>
                                    <TableCell>
                                        <Badge
                                            className={getDifficultyClass(
                                                problemStatement.difficulty,
                                            )}
                                        >
                                            {problemStatement.difficulty}
                                        </Badge>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            </div>
        </div>
    );
}

export default Problems;
