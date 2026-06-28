import importlib
import asyncio
import os
import sys
import tempfile
from contextlib import contextmanager

import httpx


class AsyncASGITestClient:
    def __init__(self, app):
        self._transport = httpx.ASGITransport(app=app)
        self._client = httpx.AsyncClient(
            transport=self._transport,
            base_url="http://testserver",
        )

    def request(self, method: str, url: str, **kwargs):
        return asyncio.run(self._client.request(method, url, **kwargs))

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def close(self):
        asyncio.run(self._client.aclose())


@contextmanager
def isolated_app(env_overrides=None):
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "phase2d.db")
        old_env = {
            "DB_PATH": os.getenv("DB_PATH"),
            "DEV_EXPOSE_OTP": os.getenv("DEV_EXPOSE_OTP"),
        }
        env_overrides = env_overrides or {}
        for key in env_overrides:
            old_env.setdefault(key, os.getenv(key))
        os.environ["DB_PATH"] = db_path
        os.environ["DEV_EXPOSE_OTP"] = "true"
        for key, value in env_overrides.items():
            os.environ[key] = str(value)
        try:
            for module_name in ("src.main", "src.config"):
                if module_name in sys.modules:
                    del sys.modules[module_name]

            config_module = importlib.import_module("src.config")
            importlib.reload(config_module)
            main_module = importlib.import_module("src.main")

            client = AsyncASGITestClient(main_module.app)
            try:
                yield main_module, client
            finally:
                client.close()
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def seed_problem(main_module, problem_id: str = "two-sum") -> None:
    conn = main_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO problems (
            problem_id, title, topic, pattern, difficulty, tags, description, function_name, test_cases
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            problem_id,
            "Two sum",
            "Arrays",
            "Hash Map",
            "Easy",
            "arrays,hashmap",
            "Find two indices with target sum.",
            "solve",
            '[{"input":[[2,7,11,15],9],"expected":[0,1]}]',
        ),
    )
    conn.commit()
    conn.close()


def register_and_login(client, email: str, password: str = "demo123", name: str = "Demo User"):
    register = client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "target_level": "medium",
        },
    )
    assert register.status_code == 200, register.text
    data = register.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "email": email,
        "password": password,
    }
