"""Limited Python judge for capstone demo submissions."""

import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Dict, List


class JudgeService:
    """Runs function-style Python submissions against stored test cases."""

    def __init__(self, timeout_seconds: int = 3):
        self.timeout_seconds = timeout_seconds

    def run_python(self, code: str, function_name: str, test_cases_json: str) -> Dict:
        """Execute submitted Python code against JSON test cases."""
        try:
            test_cases = json.loads(test_cases_json or "[]")
        except json.JSONDecodeError:
            return {
                "verdict": "Runtime Error",
                "runtime_ms": 0,
                "output": {"error": "Invalid problem test cases JSON"},
            }

        if not isinstance(test_cases, list) or not test_cases:
            return {
                "verdict": "Manual Review",
                "runtime_ms": 0,
                "output": {"error": "No executable test cases configured"},
            }

        payload = {
            "code": code,
            "function_name": function_name or "solve",
            "test_cases": test_cases,
        }

        runner = textwrap.dedent(
            """
            import contextlib
            import io
            import json
            import traceback
            import collections
            import heapq
            import bisect
            import itertools
            import math
            import typing

            ALLOWED_IMPORTS = {"typing", "collections", "heapq", "bisect", "itertools", "math"}

            def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
                root = name.split(".")[0]
                if root in ALLOWED_IMPORTS:
                    return __import__(name, globals, locals, fromlist, level)
                raise ImportError(f"Import '{name}' is not allowed in demo judge")

            SAFE_BUILTINS = {
                "__import__": safe_import,
                "abs": abs,
                "all": all,
                "any": any,
                "bool": bool,
                "chr": chr,
                "dict": dict,
                "divmod": divmod,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "int": int,
                "isinstance": isinstance,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "ord": ord,
                "pow": pow,
                "print": print,
                "range": range,
                "reversed": reversed,
                "round": round,
                "set": set,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "zip": zip,
            }

            payload = json.loads(open("payload.json", encoding="utf-8").read())
            namespace = {
                "__name__": "__submission__",
                "__builtins__": SAFE_BUILTINS,
                "collections": collections,
                "heapq": heapq,
                "bisect": bisect,
                "itertools": itertools,
                "math": math,
                "List": typing.List,
                "Dict": typing.Dict,
                "Set": typing.Set,
                "Tuple": typing.Tuple,
                "Optional": typing.Optional,
            }

            try:
                exec(payload["code"], namespace)
                fn = namespace.get(payload["function_name"])
                if not callable(fn):
                    raise ValueError(f"Function '{payload['function_name']}' not found")

                results = []
                for index, case in enumerate(payload["test_cases"], start=1):
                    args = case.get("input", [])
                    if not isinstance(args, list):
                        args = [args]

                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        actual = fn(*args)

                    expected = case.get("expected")
                    passed = actual == expected
                    results.append({
                        "case": index,
                        "passed": passed,
                        "input": args,
                        "expected": expected,
                        "actual": actual,
                        "stdout": stdout.getvalue(),
                    })
                    if not passed:
                        break

                verdict = "Accepted" if all(result["passed"] for result in results) else "Wrong Answer"
                print(json.dumps({"verdict": verdict, "results": results}))
            except Exception:
                print(json.dumps({
                    "verdict": "Runtime Error",
                    "error": traceback.format_exc(limit=4),
                }))
            """
        )

        started_at = time.perf_counter()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "payload.json").write_text(json.dumps(payload), encoding="utf-8")
            (tmp_path / "runner.py").write_text(runner, encoding="utf-8")

            try:
                completed = subprocess.run(
                    [sys.executable, "runner.py"],
                    cwd=tmp_path,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env={"PYTHONIOENCODING": "utf-8"},
                )
            except subprocess.TimeoutExpired:
                return {
                    "verdict": "Time Limit Exceeded",
                    "runtime_ms": int((time.perf_counter() - started_at) * 1000),
                    "output": {"error": f"Exceeded {self.timeout_seconds}s timeout"},
                }

        runtime_ms = int((time.perf_counter() - started_at) * 1000)
        raw_output = completed.stdout.strip()
        try:
            output = json.loads(raw_output.splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            output = {
                "verdict": "Runtime Error",
                "error": completed.stderr or raw_output or "Judge produced no output",
            }

        return {
            "verdict": output.get("verdict", "Runtime Error"),
            "runtime_ms": runtime_ms,
            "output": output,
        }

    @staticmethod
    def summarize_error_type(verdict: str) -> str:
        if verdict == "Accepted":
            return None
        if verdict == "Time Limit Exceeded":
            return "timeout"
        if verdict == "Runtime Error":
            return "runtime-error"
        if verdict == "Wrong Answer":
            return "wrong-answer"
        return "manual-review"
