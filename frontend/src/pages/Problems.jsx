import { useMemo, useState } from "react";
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
import { Button } from "@/components/ui/button.jsx";
import { Check, ChevronDown, ChevronRight, LibraryBig } from "lucide-react";

function Problems() {
    const problemStatements = useLoaderData();
    const navigate = useNavigate();

    const [expandedTopics, setExpandedTopics] = useState({});
    const [expandedPatterns, setExpandedPatterns] = useState({});

    const groupedTopics = useMemo(() => {
        const topicMap = new Map();

        for (const problem of problemStatements || []) {
            const topic = (problem.topic || "Uncategorized").trim();
            const pattern = (problem.pattern || "Unspecified").trim();

            if (!topicMap.has(topic)) {
                topicMap.set(topic, new Map());
            }
            const patternMap = topicMap.get(topic);
            if (!patternMap.has(pattern)) {
                patternMap.set(pattern, []);
            }
            patternMap.get(pattern).push(problem);
        }

        return Array.from(topicMap.entries())
            .map(([topic, patternMap]) => {
                const patterns = Array.from(patternMap.entries())
                    .map(([pattern, problems]) => {
                        const sorted = [...problems].sort((a, b) =>
                            a.title.localeCompare(b.title),
                        );
                        const solved = sorted.filter((item) => item.solved).length;
                        return {
                            pattern,
                            problems: sorted,
                            count: sorted.length,
                            solved,
                        };
                    })
                    .sort(
                        (a, b) =>
                            b.count - a.count ||
                            a.pattern.localeCompare(b.pattern),
                    );

                const count = patterns.reduce((acc, item) => acc + item.count, 0);
                const solved = patterns.reduce((acc, item) => acc + item.solved, 0);

                return {
                    topic,
                    patterns,
                    count,
                    solved,
                };
            })
            .sort((a, b) => b.count - a.count || a.topic.localeCompare(b.topic));
    }, [problemStatements]);

    const getDifficultyClass = (difficulty) => {
        if (difficulty === "Easy") {
            return "bg-emerald-100 text-emerald-800 hover:bg-emerald-100";
        }
        if (difficulty === "Medium") {
            return "bg-amber-100 text-amber-800 hover:bg-amber-100";
        }
        return "bg-rose-100 text-rose-800 hover:bg-rose-100";
    };

    const isTopicExpanded = (topic, index) => {
        if (expandedTopics[topic] !== undefined) {
            return expandedTopics[topic];
        }
        return index === 0;
    };

    const patternKey = (topic, pattern) => `${topic}::${pattern}`;

    const isPatternExpanded = (topic, pattern, topicIndex, patternIndex) => {
        const key = patternKey(topic, pattern);
        if (expandedPatterns[key] !== undefined) {
            return expandedPatterns[key];
        }
        return topicIndex === 0 && patternIndex === 0;
    };

    const toggleTopic = (topic, index) => {
        const current = isTopicExpanded(topic, index);
        setExpandedTopics((prev) => ({
            ...prev,
            [topic]: !current,
        }));
    };

    const togglePattern = (topic, pattern, topicIndex, patternIndex) => {
        const key = patternKey(topic, pattern);
        const current = isPatternExpanded(topic, pattern, topicIndex, patternIndex);
        setExpandedPatterns((prev) => ({
            ...prev,
            [key]: !current,
        }));
    };

    const expandAll = () => {
        const nextTopics = {};
        const nextPatterns = {};

        groupedTopics.forEach((topicGroup) => {
            nextTopics[topicGroup.topic] = true;
            topicGroup.patterns.forEach((patternGroup) => {
                nextPatterns[patternKey(topicGroup.topic, patternGroup.pattern)] = true;
            });
        });

        setExpandedTopics(nextTopics);
        setExpandedPatterns(nextPatterns);
    };

    const collapseAll = () => {
        const nextTopics = {};
        const nextPatterns = {};

        groupedTopics.forEach((topicGroup) => {
            nextTopics[topicGroup.topic] = false;
            topicGroup.patterns.forEach((patternGroup) => {
                nextPatterns[patternKey(topicGroup.topic, patternGroup.pattern)] = false;
            });
        });

        setExpandedTopics(nextTopics);
        setExpandedPatterns(nextPatterns);
    };

    if (problemStatements == null) {
        return (
            <div className="flex h-full-w-nav w-screen items-center justify-center">
                An error occurred while fetching problem statements
            </div>
        );
    }

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
                        Problems are grouped by topic and pattern. Expand a
                        topic, then pattern, to browse and open problems.
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                        <Badge variant="secondary" className="w-max">
                            {problemStatements.length} problems available
                        </Badge>
                        <Badge variant="outline" className="w-max">
                            {groupedTopics.length} topics
                        </Badge>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={expandAll}>
                        Expand all
                    </Button>
                    <Button variant="outline" size="sm" onClick={collapseAll}>
                        Collapse all
                    </Button>
                </div>

                <div className="flex flex-col gap-3">
                    {groupedTopics.map((topicGroup, topicIndex) => {
                        const topicExpanded = isTopicExpanded(topicGroup.topic, topicIndex);
                        return (
                            <section
                                key={topicGroup.topic}
                                className="overflow-hidden rounded-md border border-border bg-card"
                            >
                                <button
                                    type="button"
                                    onClick={() => toggleTopic(topicGroup.topic, topicIndex)}
                                    className="flex w-full items-center justify-between gap-3 border-b border-border px-4 py-3 text-left hover:bg-muted/40"
                                >
                                    <div className="flex items-center gap-2">
                                        {topicExpanded ? (
                                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                        ) : (
                                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                        )}
                                        <span className="font-semibold text-foreground">
                                            {topicGroup.topic}
                                        </span>
                                    </div>
                                    <Badge variant="secondary">
                                        {topicGroup.solved}/{topicGroup.count} solved
                                    </Badge>
                                </button>

                                {topicExpanded ? (
                                    <div className="flex flex-col gap-2 p-3">
                                        {topicGroup.patterns.map((patternGroup, patternIndex) => {
                                            const patternExpanded = isPatternExpanded(
                                                topicGroup.topic,
                                                patternGroup.pattern,
                                                topicIndex,
                                                patternIndex,
                                            );

                                            return (
                                                <div
                                                    key={patternGroup.pattern}
                                                    className="overflow-hidden rounded-md border border-border"
                                                >
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            togglePattern(
                                                                topicGroup.topic,
                                                                patternGroup.pattern,
                                                                topicIndex,
                                                                patternIndex,
                                                            )
                                                        }
                                                        className="flex w-full items-center justify-between gap-3 border-b border-border bg-muted/30 px-3 py-2 text-left hover:bg-muted/50"
                                                    >
                                                        <div className="flex items-center gap-2">
                                                            {patternExpanded ? (
                                                                <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                                            ) : (
                                                                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                                            )}
                                                            <span className="text-sm font-medium text-foreground">
                                                                {patternGroup.pattern}
                                                            </span>
                                                        </div>
                                                        <Badge variant="outline">
                                                            {patternGroup.count}
                                                        </Badge>
                                                    </button>

                                                    {patternExpanded ? (
                                                        <Table>
                                                            <TableHeader>
                                                                <TableRow className="bg-muted/50">
                                                                    <TableHead>
                                                                        Problem
                                                                    </TableHead>
                                                                    <TableHead className="w-28">
                                                                        Difficulty
                                                                    </TableHead>
                                                                </TableRow>
                                                            </TableHeader>
                                                            <TableBody>
                                                                {patternGroup.problems.map(
                                                                    (problemStatement) => (
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
                                                                                    <Check className="h-4 w-4 text-primary" />
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
                                                                    ),
                                                                )}
                                                            </TableBody>
                                                        </Table>
                                                    ) : null}
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : null}
                            </section>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

export default Problems;
