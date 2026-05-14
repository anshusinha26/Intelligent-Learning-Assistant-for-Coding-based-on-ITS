import { useContext, useEffect, useState } from "react";
import { useLoaderData } from "react-router-dom";
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from "@/components/ui/resizable.jsx";
import { Button } from "@/components/ui/button.jsx";
import Editor from "@monaco-editor/react";
import { CornerUpRight, Loader2, Play } from "lucide-react";
import AuthContext from "@/context/auth-provider.jsx";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select.jsx";
import Markdown from "react-markdown";
import { ScrollArea } from "@/components/ui/scroll-area.jsx";
import { Separator } from "@/components/ui/separator.jsx";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { Textarea } from "@/components/ui/textarea";
import { apiRequest } from "@/lib/api.js";

function Code() {
    const problemStatement = useLoaderData();
    const { user } = useContext(AuthContext);
    const { toast } = useToast();
    const [submitting, setSubmitting] = useState(false);
    const [running, setRunning] = useState(false);
    const [language, setLanguage] = useState("python");
    const [tabValue, setTabValue] = useState("testcases");
    const [output, setOutput] = useState(null);
    const [customTestcase, setCustomTestcase] = useState("");
    const [dialogData, setDialogData] = useState({
        title: "",
        description: "",
    });
    const [showDialog, setShowDialog] = useState(false);
    const [code, setCode] = useState(
        () =>
            localStorage.getItem(`code-python-${problemStatement.id}`) ||
            problemStatement.starterCode?.[0]?.code ||
            "def solve(*args):\n    return None\n",
    );
    const codeBlockClass =
        "my-2 rounded-md border border-border bg-muted/70 p-3 font-code text-sm text-foreground shadow-sm";

    useEffect(() => {
        localStorage.setItem(`code-python-${problemStatement.id}`, code);
    }, [code, problemStatement.id]);

    const submit = async (isTempRun = false) => {
        if (submitting || running) {
            return;
        }
        if (isTempRun) {
            setRunning(true);
        } else {
            setSubmitting(true);
        }
        try {
            const result = await apiRequest("/submissions", {
                token: user.token,
                method: "POST",
                body: {
                    problem_id: problemStatement.id,
                    language,
                    code,
                },
            });

            setOutput([JSON.stringify(result.output, null, 2)]);
            setTabValue("output");

            if (!isTempRun) {
                setDialogData({
                    title: result.verdict,
                    description: `Executed in ${result.runtime_ms}ms`,
                });
                setShowDialog(true);
            }
            toast({
                title: result.verdict,
                description: `Executed in ${result.runtime_ms}ms`,
            });
        } catch (error) {
            setDialogData({
                title: "Error",
                description: error.message,
            });
            setShowDialog(true);
        } finally {
            setRunning(false);
            setSubmitting(false);
        }
    };

    if (!problemStatement) {
        return (
            <div className="w-screen h-full-w-nav flex justify-center align-middle items-center">
                Could not find this problem statement
            </div>
        );
    }

    return (
        <div className="w-screen h-full-w-nav">
            <AlertDialog open={showDialog} onOpenChange={setShowDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>{dialogData.title}</AlertDialogTitle>
                        <AlertDialogDescription>
                            {dialogData.description}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction>OK</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
            <ResizablePanelGroup
                direction="horizontal"
                className="border h-full w-full"
            >
                <ResizablePanel defaultSize={50}>
                    <Tabs defaultValue="problem-statement">
                        <TabsList>
                            <TabsTrigger
                                value="problem-statement"
                                className="m-0.5"
                            >
                                Problem Statement
                            </TabsTrigger>
                            <TabsTrigger value="ai" className="m-0.5">
                                Ask AI
                            </TabsTrigger>
                            <TabsTrigger value="editorials" className="m-0.5">
                                Editorials
                            </TabsTrigger>
                        </TabsList>
                        <TabsContent value="problem-statement">
                            <ScrollArea className="flex h-full w-full flex-col gap-5 pb-14">
                                <Markdown className="prose dark:prose-invert min-w-full p-6">
                                    {problemStatement.description}
                                </Markdown>
                            </ScrollArea>
                        </TabsContent>
                        <TabsContent value="ai">
                            <div className="p-6 text-muted-foreground">
                                RAG assistant integration kept on hold for final
                                phase.
                            </div>
                        </TabsContent>
                        <TabsContent value="editorials">
                            <div className="p-6 text-muted-foreground">
                                Editorials can be added after judge flow is
                                stable.
                            </div>
                        </TabsContent>
                    </Tabs>
                </ResizablePanel>
                <ResizableHandle withHandle />
                <ResizablePanel defaultSize={50}>
                    <ResizablePanelGroup direction="vertical">
                        <ResizablePanel defaultSize={50}>
                            <div className="z-0 flex flex-col h-full">
                                <div className="flex flex-row gap-2 m-1">
                                    <Select
                                        onValueChange={(value) =>
                                            setLanguage(value)
                                        }
                                        value={language}
                                    >
                                        <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Language" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="python">
                                                Python
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <Button
                                        disabled={running}
                                        className="z-10 self-end"
                                        onClick={() => submit(true)}
                                    >
                                        {running ? (
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        ) : (
                                            <Play className="mr-2 h-4 w-4" />
                                        )}
                                        Run
                                    </Button>
                                    <Button
                                        disabled={submitting}
                                        className="z-10 self-end"
                                        onClick={() => submit(false)}
                                    >
                                        {submitting ? (
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        ) : (
                                            <CornerUpRight className="mr-2 h-4 w-4" />
                                        )}
                                        Submit
                                    </Button>
                                </div>
                                <div className="h-full">
                                    <Editor
                                        theme="vs-dark"
                                        language="python"
                                        value={code}
                                        onChange={(value) =>
                                            setCode(value || "")
                                        }
                                        options={{
                                            fontFamily: "Cascadia Code",
                                            fontLigatures: true,
                                            autoIndent: "full",
                                            cursorSmoothCaretAnimation: "on",
                                            cursorBlinking: "expand",
                                        }}
                                    />
                                </div>
                            </div>
                        </ResizablePanel>
                        <ResizableHandle withHandle />
                        <ResizablePanel defaultSize={50}>
                            <Tabs value={tabValue} onValueChange={setTabValue}>
                                <TabsList>
                                    <TabsTrigger
                                        className="m-0.5"
                                        value="testcases"
                                    >
                                        Sample Testcases
                                    </TabsTrigger>
                                    <TabsTrigger
                                        className="m-0.5"
                                        value="custom-testcase"
                                    >
                                        Custom Testcase
                                    </TabsTrigger>
                                    {output != null ? (
                                        <TabsTrigger
                                            className="m-0.5"
                                            value="output"
                                        >
                                            Run Output
                                        </TabsTrigger>
                                    ) : null}
                                </TabsList>
                                <TabsContent value="testcases">
                                    <ScrollArea className="h-full items-center justify-center">
                                        <div className="p-6 pb-14">
                                            <p className="text-2xl">
                                                Sample Test Cases
                                            </p>
                                            {problemStatement.testCase.length ===
                                            0 ? (
                                                <p className="text-muted-foreground mt-3">
                                                    No executable sample tests
                                                    configured. Use manual
                                                    attempt flow from dashboard
                                                    for this item.
                                                </p>
                                            ) : (
                                                problemStatement.testCase.map(
                                                    (testCase, index) => (
                                                        <div key={testCase.id}>
                                                            <p className="mt-3 text-lg">
                                                                Test Case{" "}
                                                                {index + 1}
                                                            </p>
                                                            <div className="my-1">
                                                                Input
                                                                <div
                                                                    className={
                                                                        codeBlockClass
                                                                    }
                                                                >
                                                                    {
                                                                        testCase.input
                                                                    }
                                                                </div>
                                                                Output
                                                                <div
                                                                    className={
                                                                        codeBlockClass
                                                                    }
                                                                >
                                                                    {
                                                                        testCase.output
                                                                    }
                                                                </div>
                                                            </div>
                                                            {index !==
                                                            problemStatement
                                                                .testCase
                                                                .length -
                                                                1 ? (
                                                                <Separator className="mt-6" />
                                                            ) : null}
                                                        </div>
                                                    ),
                                                )
                                            )}
                                        </div>
                                    </ScrollArea>
                                </TabsContent>
                                <TabsContent value="custom-testcase">
                                    <ScrollArea className="flex h-full flex-col gap-5">
                                        <div className="p-6 pb-14">
                                            <Textarea
                                                value={customTestcase}
                                                onChange={(event) =>
                                                    setCustomTestcase(
                                                        event.target.value,
                                                    )
                                                }
                                                placeholder="Custom testcase execution comes with Docker judge upgrade."
                                                className="flex-1 resize-none"
                                                rows={10}
                                            />
                                        </div>
                                    </ScrollArea>
                                </TabsContent>
                                {output != null ? (
                                    <TabsContent value="output">
                                        <ScrollArea className="flex h-full flex-col gap-5">
                                            <div className="p-6 pb-14">
                                                <p className="text-2xl">
                                                    Code Output
                                                </p>
                                                {output.map((line, index) => (
                                                    <div
                                                        key={index}
                                                        className={`${codeBlockClass} whitespace-pre-wrap`}
                                                    >
                                                        {line}
                                                    </div>
                                                ))}
                                            </div>
                                        </ScrollArea>
                                    </TabsContent>
                                ) : null}
                            </Tabs>
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    );
}

export default Code;
