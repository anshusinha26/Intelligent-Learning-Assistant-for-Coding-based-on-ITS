"""Limited Python judge for capstone demo submissions."""

import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Dict

from src.config import settings


class JudgeService:
    def __init__(self, timeout_seconds: int = settings.judge_timeout_seconds):
        self.timeout_seconds = timeout_seconds
        self.max_code_size_bytes = settings.max_code_size_bytes
        self.max_test_cases = settings.judge_max_test_cases
        self.max_output_chars = settings.judge_max_output_chars
        self.memory_limit_mb = settings.judge_memory_limit_mb
        self.recursion_limit = settings.judge_recursion_limit

    def run_python(self, code: str, function_name: str, test_cases_json: str) -> Dict:
        if not code or not code.strip():
            return {
                "verdict": "Compilation Error",
                "runtime_ms": 0,
                "output": {"error": "Code cannot be empty"},
            }
        if len(code.encode("utf-8")) > self.max_code_size_bytes:
            return {
                "verdict": "Runtime Error",
                "runtime_ms": 0,
                "output": {"error": f"Code exceeds max size ({self.max_code_size_bytes} bytes)"},
            }

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
        if len(test_cases) > self.max_test_cases:
            return {
                "verdict": "Runtime Error",
                "runtime_ms": 0,
                "output": {"error": f"Too many test cases (max {self.max_test_cases})"},
            }

        payload = {
            "code": code,
            "function_name": function_name or "solve",
            "test_cases": test_cases,
            "max_output_chars": self.max_output_chars,
            "memory_limit_mb": self.memory_limit_mb,
            "recursion_limit": self.recursion_limit,
        }

        runner = textwrap.dedent(
            """
            import contextlib
            import io
            import json
            import resource
            import traceback
            import collections
            import heapq
            import bisect
            import itertools
            import math
            import sys
            import typing

            ALLOWED_IMPORTS = {"typing", "collections", "heapq", "bisect", "itertools", "math"}

            def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
                root = name.split(".")[0]
                if root in ALLOWED_IMPORTS:
                    return __import__(name, globals, locals, fromlist, level)
                raise ImportError(f"Import '{name}' is not allowed in demo judge")

            payload = json.loads(open("payload.json", encoding="utf-8").read())
            max_output_chars = int(payload.get("max_output_chars", 12000))
            memory_limit_mb = int(payload.get("memory_limit_mb", 128))
            recursion_limit = int(payload.get("recursion_limit", 2000))

            try:
                bytes_limit = memory_limit_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
                resource.setrlimit(resource.RLIMIT_DATA, (bytes_limit, bytes_limit))
                resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
            except Exception:
                pass

            sys.setrecursionlimit(recursion_limit)
            budget = {"remaining": max_output_chars}

            def _truncate(value, limit=400):
                text = str(value)
                if len(text) <= limit:
                    return text
                return text[:limit] + "...<truncated>"

            def limited_print(*args, **kwargs):
                text = " ".join(str(arg) for arg in args)
                end = kwargs.get("end", "\\n")
                chunk = text + end
                if len(chunk) > budget["remaining"]:
                    raise RuntimeError("Output limit exceeded")
                budget["remaining"] -= len(chunk)
                sys.stdout.write(chunk)

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
                "print": limited_print,
                "range": range,
                "reversed": reversed,
                "round": round,
                "set": set,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "zip": zip,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
            }

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
                        "input": _truncate(args, 600),
                        "expected": _truncate(expected, 600),
                        "actual": _truncate(actual, 600),
                        "stdout": _truncate(stdout.getvalue(), 1200),
                    })
                    if not passed:
                        break

                verdict = "Accepted" if all(result["passed"] for result in results) else "Wrong Answer"
                print(json.dumps({"verdict": verdict, "results": results}))
            except SyntaxError:
                print(json.dumps({
                    "verdict": "Compilation Error",
                    "error": traceback.format_exc(limit=3),
                }))
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
                    [sys.executable, "-I", "runner.py"],
                    cwd=tmp_path,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env={"PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0"},
                )
            except subprocess.TimeoutExpired:
                return {
                    "verdict": "Time Limit Exceeded",
                    "runtime_ms": int((time.perf_counter() - started_at) * 1000),
                    "output": {"error": f"Exceeded {self.timeout_seconds}s timeout"},
                }

        runtime_ms = int((time.perf_counter() - started_at) * 1000)
        raw_output = completed.stdout.strip()
        if len(raw_output) > self.max_output_chars * 2:
            raw_output = raw_output[: self.max_output_chars * 2] + "...<truncated>"
        try:
            output = json.loads(raw_output.splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            output = {
                "verdict": "Runtime Error",
                "error": (completed.stderr or raw_output or "Judge produced no output")[: self.max_output_chars],
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
        if verdict == "Compilation Error":
            return "compilation-error"
        return "manual-review"
