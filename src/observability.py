import time
from typing import Tuple

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry(auto_describe=True)

APP_UP = Gauge("ila_app_up", "Application availability", registry=REGISTRY)
APP_STARTUPS_TOTAL = Counter("ila_app_startups_total", "Startup event count", registry=REGISTRY)
APP_SHUTDOWNS_TOTAL = Counter("ila_app_shutdowns_total", "Shutdown event count", registry=REGISTRY)
APP_INFO = Gauge(
    "ila_app_info",
    "Application info",
    labelnames=("name", "env", "version"),
    registry=REGISTRY,
)

HTTP_REQUESTS_TOTAL = Counter(
    "ila_http_requests_total",
    "HTTP requests",
    labelnames=("method", "path", "status"),
    registry=REGISTRY,
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "ila_http_request_duration_seconds",
    "HTTP request latency",
    labelnames=("method", "path"),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    registry=REGISTRY,
)
SLOW_REQUESTS_TOTAL = Counter(
    "ila_slow_requests_total",
    "Slow requests above configured threshold",
    labelnames=("method", "path"),
    registry=REGISTRY,
)

DB_QUERIES_TOTAL = Counter(
    "ila_db_queries_total",
    "Database queries",
    labelnames=("statement",),
    registry=REGISTRY,
)
DB_QUERY_DURATION_SECONDS = Histogram(
    "ila_db_query_duration_seconds",
    "Database query latency",
    labelnames=("statement",),
    buckets=(0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 1),
    registry=REGISTRY,
)
DB_SLOW_QUERIES_TOTAL = Counter(
    "ila_db_slow_queries_total",
    "Slow database queries above configured threshold",
    labelnames=("statement",),
    registry=REGISTRY,
)

JUDGE_EXECUTIONS_TOTAL = Counter(
    "ila_judge_executions_total",
    "Judge executions by verdict",
    labelnames=("verdict",),
    registry=REGISTRY,
)
JUDGE_RUNTIME_SECONDS = Histogram(
    "ila_judge_runtime_seconds",
    "Judge runtime in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    registry=REGISTRY,
)

RAG_QUERIES_TOTAL = Counter(
    "ila_rag_queries_total",
    "RAG queries by source and status",
    labelnames=("source", "status"),
    registry=REGISTRY,
)
RAG_QUERY_DURATION_SECONDS = Histogram(
    "ila_rag_query_duration_seconds",
    "RAG query duration in seconds",
    labelnames=("source",),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    registry=REGISTRY,
)

RECOMMENDATION_GENERATIONS_TOTAL = Counter(
    "ila_recommendation_generations_total",
    "Recommendation generation calls",
    labelnames=("refresh",),
    registry=REGISTRY,
)
RECOMMENDATION_ITEMS_GENERATED_TOTAL = Counter(
    "ila_recommendation_items_generated_total",
    "Total recommendation rows generated",
    registry=REGISTRY,
)
RECOMMENDATION_COMPLETIONS_TOTAL = Counter(
    "ila_recommendation_completions_total",
    "Recommendations completed",
    registry=REGISTRY,
)

STARTED_AT_SECONDS = Gauge(
    "ila_started_at_seconds",
    "Unix timestamp when app started",
    registry=REGISTRY,
)


def _statement_type(sql: str) -> str:
    if not sql:
        return "unknown"
    token = sql.strip().split(None, 1)
    if not token:
        return "unknown"
    return token[0].lower()


def mark_startup(app_name: str, app_env: str, app_version: str) -> None:
    APP_STARTUPS_TOTAL.inc()
    APP_UP.set(1)
    STARTED_AT_SECONDS.set(time.time())
    APP_INFO.labels(name=app_name, env=app_env, version=app_version).set(1)


def mark_shutdown() -> None:
    APP_SHUTDOWNS_TOTAL.inc()
    APP_UP.set(0)


def record_http_request(method: str, path: str, status_code: int, elapsed_ms: int) -> None:
    HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=str(status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(max(elapsed_ms, 0) / 1000.0)


def record_slow_request(method: str, path: str) -> None:
    SLOW_REQUESTS_TOTAL.labels(method=method, path=path).inc()


def record_db_query(sql: str, elapsed_ms: float, slow_threshold_ms: int) -> None:
    statement = _statement_type(sql)
    DB_QUERIES_TOTAL.labels(statement=statement).inc()
    DB_QUERY_DURATION_SECONDS.labels(statement=statement).observe(max(elapsed_ms, 0.0) / 1000.0)
    if elapsed_ms >= slow_threshold_ms:
        DB_SLOW_QUERIES_TOTAL.labels(statement=statement).inc()


def record_judge_execution(verdict: str, runtime_ms: int) -> None:
    JUDGE_EXECUTIONS_TOTAL.labels(verdict=verdict).inc()
    JUDGE_RUNTIME_SECONDS.observe(max(runtime_ms, 0) / 1000.0)


def record_rag_query(source: str, error: str, elapsed_ms: int) -> None:
    status = "ok" if not error else "error"
    src = source or "unknown"
    RAG_QUERIES_TOTAL.labels(source=src, status=status).inc()
    RAG_QUERY_DURATION_SECONDS.labels(source=src).observe(max(elapsed_ms, 0) / 1000.0)


def record_recommendation_generation(count: int, refresh: bool) -> None:
    RECOMMENDATION_GENERATIONS_TOTAL.labels(refresh=str(bool(refresh)).lower()).inc()
    RECOMMENDATION_ITEMS_GENERATED_TOTAL.inc(max(count, 0))


def record_recommendation_completion() -> None:
    RECOMMENDATION_COMPLETIONS_TOTAL.inc()


def render_metrics() -> Tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
