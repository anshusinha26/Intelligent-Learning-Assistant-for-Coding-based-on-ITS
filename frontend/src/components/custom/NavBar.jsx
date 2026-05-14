import { Button } from "@/components/ui/button.jsx";
import { Sheet, SheetTrigger, SheetContent } from "@/components/ui/sheet.jsx";
import AuthContext from "@/context/auth-provider.jsx";
import { ArrowRight, BrainCircuit, LogOut, Menu, Zap } from "lucide-react";
import { useContext, useEffect, useRef } from "react";
import { Link, useNavigate, useNavigation } from "react-router-dom";
import LoadingBar from "react-top-loading-bar";
import NumberTicker from "@/components/ui/number-ticker";

export default function NavBar() {
    const { user, setUser } = useContext(AuthContext);
    const { state: navState } = useNavigation();
    const loaderRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        if (navState === "loading") {
            loaderRef.current?.continuousStart();
        } else {
            loaderRef.current?.complete();
        }
    }, [navState]);

    const logout = () => {
        setUser({
            id: null,
            email: null,
            name: null,
            token: null,
            isAuthenticated: false,
            points: 0,
        });
        navigate("/");
    };

    const links = [
        { to: "/", label: "Home" },
        { to: "/problems", label: "Problems" },
        { to: "/dashboard", label: "Dashboard", auth: true },
        { to: "/submissions", label: "Submissions", auth: true },
    ].filter((link) => !link.auth || user.isAuthenticated);

    return (
        <header className="sticky top-0 z-50 w-full border-b border-border/80 bg-background/90 backdrop-blur-xl">
            <LoadingBar color="#0f8f7e" ref={loaderRef} />
            <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-6">
                <div className="flex-1">
                    <Link
                        to="/"
                        className="flex w-max items-center gap-2 text-foreground"
                    >
                        <span className="flex h-9 w-9 items-center justify-center rounded-md border border-primary/25 bg-primary/10 text-primary">
                            <BrainCircuit className="h-5 w-5" />
                        </span>
                        <span className="font-semibold">ILA Coding</span>
                    </Link>
                </div>
                <nav className="hidden items-center justify-center gap-6 text-sm font-medium md:flex flex-1">
                    {links.map((link) => (
                        <Link
                            key={link.to}
                            to={link.to}
                            className="relative text-muted-foreground transition-colors duration-300 after:absolute after:-bottom-1 after:left-0 after:h-0.5 after:w-0 after:bg-primary after:transition-all hover:text-foreground hover:after:w-full"
                        >
                            {link.label}
                        </Link>
                    ))}
                </nav>
                <div className="flex items-center justify-end flex-1 gap-4">
                    {!user.isAuthenticated ? (
                        <div className="flex gap-4">
                            <Button variant="outline" asChild>
                                <Link to="/login">Login</Link>
                            </Button>
                            <Button className="group" asChild>
                                <Link to="/register">
                                    Register
                                    <ArrowRight className="ml-2 z-10 group-hover:ml-3 duration-200" />
                                </Link>
                            </Button>
                        </div>
                    ) : (
                        <div className="flex flex-row items-center gap-4">
                            <button
                                className="flex flex-row gap-1 items-center group cursor-pointer"
                                onClick={() => navigate("/dashboard")}
                            >
                                <Zap
                                    className="fill-primary/20 stroke-primary duration-500 group-hover:fill-primary"
                                    height={20}
                                />
                                <NumberTicker value={user.points || 0} />
                            </button>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="rounded-full"
                                onClick={logout}
                            >
                                <LogOut />
                            </Button>
                        </div>
                    )}
                    <Sheet>
                        <SheetTrigger asChild>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="rounded-md md:hidden"
                            >
                                <Menu className="h-5 w-5 text-muted-foreground" />
                                <span className="sr-only">
                                    Toggle navigation menu
                                </span>
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="md:hidden">
                            <div className="grid gap-4 p-4">
                                {links.map((link) => (
                                    <Link
                                        key={link.to}
                                        to={link.to}
                                        className="text-sm font-medium text-muted-foreground hover:text-foreground"
                                    >
                                        {link.label}
                                    </Link>
                                ))}
                            </div>
                        </SheetContent>
                    </Sheet>
                </div>
            </div>
        </header>
    );
}
