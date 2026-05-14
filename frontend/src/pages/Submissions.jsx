import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table.jsx";
import { Badge } from "@/components/ui/badge";
import { useLoaderData, useNavigate } from "react-router-dom";

function Submissions() {
    const { submissions } = useLoaderData();
    const navigate = useNavigate();

    return (
        <div className="w-screen flex justify-center">
            {submissions.length > 0 ? (
                <div className="text-2xl w-[1152px] max-w-6xl flex items-center justify-center py-5 flex-col gap-5">
                    <p>Your Submissions</p>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Problem</TableHead>
                                <TableHead className="w-32">Status</TableHead>
                                <TableHead className="w-32">
                                    Execution Time
                                </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {submissions.map((submission) => (
                                <TableRow
                                    key={submission.submission_id}
                                    onClick={() =>
                                        navigate(
                                            `/problem/${submission.problem_id}`,
                                        )
                                    }
                                    className="group hover:cursor-pointer"
                                >
                                    <TableCell className="group-hover:underline underline-offset-2 decoration-primary overflow-ellipsis w-full max-w-[90%] flex flex-row gap-2 items-center">
                                        {submission.title}
                                    </TableCell>
                                    <TableCell>
                                        <Badge
                                            className={
                                                submission.verdict ===
                                                "Accepted"
                                                    ? "bg-primary"
                                                    : "bg-red-500"
                                            }
                                        >
                                            {submission.verdict}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        {submission.runtime_ms
                                            ? `${submission.runtime_ms} ms`
                                            : "Unknown"}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            ) : (
                <p className="text-2xl py-5">
                    Submit your first solution and view it here
                </p>
            )}
        </div>
    );
}

export default Submissions;
