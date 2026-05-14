import { useLoaderData } from "react-router-dom";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import { CalendarCheck, CheckCircle2, Flame, Gauge } from "lucide-react";

function Dashboard() {
    const { dashboard, weaknesses, revisions } = useLoaderData();
    const cards = [
        {
            label: "Problems Solved",
            value: dashboard.total_problems_solved,
            icon: CheckCircle2,
        },
        {
            label: "Success Rate",
            value: `${dashboard.success_rate.toFixed(1)}%`,
            icon: Gauge,
        },
        {
            label: "Current Streak",
            value: dashboard.current_streak,
            icon: Flame,
        },
        {
            label: "Due Revisions",
            value: revisions.stats.due_revisions,
            icon: CalendarCheck,
        },
    ];

    return (
        <div className="min-h-full-w-nav w-full bg-background px-4 py-8 md:px-6">
            <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
                <div className="flex flex-col gap-2">
                    <Badge variant="secondary" className="w-max">
                        ITS learner state
                    </Badge>
                    <h1 className="text-3xl font-bold tracking-normal">
                        Learning Dashboard
                    </h1>
                    <p className="max-w-3xl text-muted-foreground">
                        ITS insights from attempts, submissions, weaknesses, and
                        revision schedule.
                    </p>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
                    {cards.map((card) => {
                        const Icon = card.icon;
                        return (
                            <Card key={card.label}>
                                <CardHeader className="gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                                        <Icon className="h-5 w-5" />
                                    </div>
                                    <CardDescription>
                                        {card.label}
                                    </CardDescription>
                                    <CardTitle className="text-3xl">
                                        {card.value}
                                    </CardTitle>
                                </CardHeader>
                            </Card>
                        );
                    })}
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
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
                                    className="flex items-center justify-between rounded-md border p-3"
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
                                        className="flex items-center justify-between rounded-md border p-3"
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
