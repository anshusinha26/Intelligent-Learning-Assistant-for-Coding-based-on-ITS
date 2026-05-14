import { useLoaderData } from "react-router-dom";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";

function Dashboard() {
    const { dashboard, weaknesses, revisions } = useLoaderData();
    const cards = [
        {
            label: "Problems Solved",
            value: dashboard.total_problems_solved,
        },
        {
            label: "Success Rate",
            value: `${dashboard.success_rate.toFixed(1)}%`,
        },
        {
            label: "Current Streak",
            value: dashboard.current_streak,
        },
        {
            label: "Due Revisions",
            value: revisions.stats.due_revisions,
        },
    ];

    return (
        <div className="w-screen flex justify-center">
            <div className="w-[1152px] max-w-6xl py-5 px-4 flex flex-col gap-5">
                <div>
                    <h1 className="text-2xl font-semibold">
                        Learning Dashboard
                    </h1>
                    <p className="text-muted-foreground">
                        ITS insights from attempts, submissions, weaknesses, and
                        revision schedule.
                    </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {cards.map((card) => (
                        <Card key={card.label}>
                            <CardHeader>
                                <CardDescription>{card.label}</CardDescription>
                                <CardTitle>{card.value}</CardTitle>
                            </CardHeader>
                        </Card>
                    ))}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Weak Areas</CardTitle>
                            <CardDescription>
                                Lowest mastery areas first
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="flex flex-col gap-3">
                            {(weaknesses.weaknesses || []).map((item) => (
                                <div
                                    key={item.topic}
                                    className="flex items-center justify-between border rounded-md p-3"
                                >
                                    <div>
                                        <p className="font-medium">
                                            {item.topic}
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            {item.attempts_count} attempts ·{" "}
                                            {item.success_rate}% success
                                        </p>
                                    </div>
                                    <Badge>
                                        {Math.round(
                                            item.mastery_score * 100,
                                        )}
                                        %
                                    </Badge>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                            <CardTitle>Revision Queue</CardTitle>
                            <CardDescription>
                                Spaced repetition tasks due now
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="flex flex-col gap-3">
                            {(revisions.revisions || []).length === 0 ? (
                                <p className="text-muted-foreground">
                                    No revisions due right now.
                                </p>
                            ) : (
                                revisions.revisions.map((item) => (
                                    <div
                                        key={item.schedule_id}
                                        className="flex items-center justify-between border rounded-md p-3"
                                    >
                                        <div>
                                            <p className="font-medium">
                                                {item.title}
                                            </p>
                                            <p className="text-sm text-muted-foreground">
                                                Due {item.next_review_date}
                                            </p>
                                        </div>
                                        <Badge>{item.difficulty}</Badge>
                                    </div>
                                ))
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
