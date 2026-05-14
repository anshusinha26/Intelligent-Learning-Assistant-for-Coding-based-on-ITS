import { Button } from "@/components/ui/button";
import {
    ArrowRight,
    BrainCircuit,
    CalendarCheck,
    CheckCircle2,
    LineChart,
    Target,
} from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { TypeAnimation } from "react-type-animation";

function Home() {
    const learnerTrace1 = `> learner_model.recompute(user)
attempt recorded: Wrong Answer
weak topic: Dynamic Programming`;
    const learnerTrace2 = `> recommender.score(unseen)
630 curated problems scanned
weakness weight applied
next: Longest Substring
review plan refreshed`;
    const features = [
        {
            icon: Target,
            label: "Curated DSA bank",
            value: "630 problems",
        },
        {
            icon: BrainCircuit,
            label: "ITS learner model",
            value: "weakness tracking",
        },
        {
            icon: CalendarCheck,
            label: "Review scheduler",
            value: "spaced practice",
        },
    ];
    const cycle = [
        "Record each coding attempt",
        "Recompute topic and pattern mastery",
        "Score unseen problems by weakness",
        "Build a focused revision queue",
    ];

    return (
        <div className="min-h-full-w-nav w-full overflow-hidden bg-background text-foreground">
            <div className="border-b border-border bg-[linear-gradient(135deg,hsl(var(--background))_0%,hsl(var(--secondary))_48%,hsl(var(--background))_100%)]">
                <div className="mx-auto grid min-h-[calc(100vh-65px)] w-full max-w-7xl grid-cols-1 items-center gap-10 px-4 py-10 md:px-6 lg:grid-cols-[1.02fr_0.98fr] lg:py-14">
                    <div className="space-y-7">
                        <motion.div
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.45 }}
                            className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
                        >
                            <BrainCircuit className="h-4 w-4" />
                            ITS-powered coding practice
                        </motion.div>

                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="max-w-3xl text-4xl font-bold tracking-normal text-foreground sm:text-5xl xl:text-6xl"
                        >
                            Intelligent Learning Assistant for Coding
                        </motion.h1>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="max-w-2xl text-base leading-8 text-muted-foreground md:text-xl"
                        >
                            Practice from a structured DSA bank, submit Python
                            solutions, and let the learner model convert every
                            attempt into weaknesses, recommendations, and review
                            plans.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.4 }}
                            className="flex flex-col gap-3 sm:flex-row"
                        >
                            <Button className="group h-11 px-5" asChild>
                                <Link to="/problems">
                                    Start Adaptive Practice
                                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                                </Link>
                            </Button>
                            <Button
                                className="h-11 px-5"
                                variant="outline"
                                asChild
                            >
                                <Link to="/dashboard">
                                    View Learning Dashboard
                                    <LineChart className="ml-2 h-4 w-4" />
                                </Link>
                            </Button>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.55 }}
                            className="grid max-w-2xl grid-cols-1 gap-3 sm:grid-cols-3"
                        >
                            {features.map((feature) => {
                                const FeatureIcon = feature.icon;
                                return (
                                    <div
                                        key={feature.label}
                                        className="rounded-md border border-border bg-card/80 p-4 shadow-sm"
                                    >
                                        <FeatureIcon className="mb-3 h-5 w-5 text-primary" />
                                        <p className="text-sm font-semibold">
                                            {feature.value}
                                        </p>
                                        <p className="mt-1 text-xs text-muted-foreground">
                                            {feature.label}
                                        </p>
                                    </div>
                                );
                            })}
                        </motion.div>
                    </div>

                    <div className="space-y-4">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="overflow-hidden rounded-md border border-border bg-card shadow-xl"
                        >
                            <div className="flex items-center justify-between border-b border-border bg-muted/60 px-4 py-3">
                                <div>
                                    <p className="text-sm font-semibold">
                                        Adaptive tutoring cycle
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Live learner-state update
                                    </p>
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
                                    <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                                    <span className="h-2.5 w-2.5 rounded-full bg-primary" />
                                </div>
                            </div>
                            <div className="min-h-56 p-5 font-code text-sm leading-7 text-primary">
                                <TypeAnimation
                                    style={{
                                        whiteSpace: "pre-line",
                                        minHeight: "168px",
                                        display: "block",
                                    }}
                                    sequence={[
                                        learnerTrace1,
                                        900,
                                        learnerTrace2,
                                    ]}
                                    speed={10}
                                />
                            </div>
                        </motion.div>

                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            {cycle.map((item, index) => (
                                <div
                                    key={item}
                                    className="flex items-center gap-3 rounded-md border border-border bg-card/80 p-3 text-sm shadow-sm"
                                >
                                    <CheckCircle2 className="h-4 w-4 shrink-0 text-primary" />
                                    <span>
                                        {index + 1}. {item}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Home;
