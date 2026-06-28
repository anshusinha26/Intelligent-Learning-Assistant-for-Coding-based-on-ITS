from pathlib import Path

from scripts.phase5_performance_reliability import Phase5Config, run_phase5_validation
from src.rag_service import RAGService


def test_phase5_small_validation_smoke():
    cfg = Phase5Config(
        concurrent_levels=(20, 50),
        worker_limit=25,
        hot_path_iterations=5,
        memory_rag_queries=80,
        bank_path=Path("data/premium/problem_bank.json"),
    )
    report = run_phase5_validation(cfg)
    assert "part_1_load_testing" in report
    assert "part_5_fault_injection" in report
    assert "quality_gate" in report
    assert report["quality_gate"]["maximum_concurrent_users_supported"] >= 20
    assert report["quality_gate"]["p95_latency_ms"] >= 0


def test_rag_thread_state_bounded():
    service = RAGService(
        enabled=True,
        mode="local",
        base_url="http://127.0.0.1:0",
        org_id="phase5",
        agent_id="phase5",
        service_token="",
        allow_full_solutions=False,
        enforce_hint_progression=True,
        max_question_chars=2000,
        max_thread_state=120,
    )
    for idx in range(300):
        service.query(
            user_id=1,
            thread_id=f"thread-{idx}",
            question="Need a gentle hint.",
            hint_level=1,
            want_full_solution=False,
            problem_context={"title": "Two Sum", "topic": "Arrays & Hashing", "pattern": "Hash Map", "difficulty": "Easy"},
        )
    assert len(service._thread_hint_levels) <= 120
