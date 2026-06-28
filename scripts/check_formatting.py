#!/usr/bin/env python3
import os
import sys


EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".sh",
    ".txt",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    ".venv_test",
    "node_modules",
    "frontend/node_modules",
    "frontend/dist",
    "dist",
    "__pycache__",
}

INCLUDE_DIRS = ["scripts", "docs", ".github", "migrations", "observability", "tests"]
INCLUDE_ROOT_FILES = {
    "Dockerfile",
    ".dockerignore",
    "docker-compose.yml",
    ".env.example",
    ".env.development.example",
    ".env.production.example",
    "frontend/Dockerfile",
    "frontend/nginx.conf",
    "frontend/.dockerignore",
    "src/config.py",
    "src/main.py",
    "src/database.py",
    "src/observability.py",
    "src/migrations.py",
    "src/security.py",
    "src/auth.py",
    "src/judge.py",
    "src/rag_service.py",
    "src/models.py",
}


def should_skip(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized == d or normalized.startswith(f"{d}/") for d in SKIP_DIRS)


def iter_files(root: str):
    for filename in INCLUDE_ROOT_FILES:
        abs_path = os.path.join(root, filename)
        if os.path.exists(abs_path):
            yield abs_path, filename

    for include_dir in INCLUDE_DIRS:
        abs_include_dir = os.path.join(root, include_dir)
        if not os.path.isdir(abs_include_dir):
            continue
        for current_root, dirs, files in os.walk(abs_include_dir):
            rel_root = os.path.relpath(current_root, root)
            if rel_root == ".":
                rel_root = ""
            dirs[:] = [d for d in dirs if not should_skip(f"{rel_root}/{d}".strip("/"))]
            for filename in files:
                rel_path = f"{rel_root}/{filename}".strip("/")
                if should_skip(rel_path):
                    continue
                _, ext = os.path.splitext(filename)
                if ext in EXTENSIONS:
                    yield os.path.join(root, rel_path), rel_path


def main() -> int:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    violations = []
    for abs_path, rel_path in iter_files(project_root):
        with open(abs_path, "rb") as handle:
            content = handle.read()
        if b"\r\n" in content:
            violations.append(f"{rel_path}: uses CRLF line endings")
        if content and not content.endswith(b"\n"):
            violations.append(f"{rel_path}: missing trailing newline")
        lines = content.splitlines()
        for index, line in enumerate(lines, start=1):
            if line.rstrip(b" \t") != line:
                violations.append(f"{rel_path}:{index}: trailing whitespace")
            if b"\t" in line:
                violations.append(f"{rel_path}:{index}: tab character")

    if violations:
        print("Formatting violations detected:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Formatting checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
