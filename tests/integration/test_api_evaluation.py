"""Integration tests for quality evaluation endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from keepcontext_ai.context.schemas import EnrichedContextResult
from keepcontext_ai.graph.schemas import Entity, GraphResult
from keepcontext_ai.memory.schemas import MemoryEntry, MemoryResult, MemoryType


def _memory_result(memory_id: str, content: str) -> MemoryResult:
    return MemoryResult(
        entry=MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=MemoryType.DECISION,
            created_at="2026-01-01T00:00:00+00:00",
        ),
        score=0.9,
    )


def _create_eval_test_app(llm_available: bool = True) -> FastAPI:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    from keepcontext_ai.api.routes import evaluation, health
    from keepcontext_ai.exceptions import AppError

    app = FastAPI(title="test-evaluation")

    retriever = MagicMock()
    retriever.query.return_value = [
        _memory_result("mem-auth-1", "Auth issues JWT access token"),
        _memory_result("mem-auth-2", "Refresh token rotation"),
    ]
    retriever.query_enriched.return_value = EnrichedContextResult(
        memory_results=[_memory_result("mem-auth-1", "Auth token validation")],
        graph_context=GraphResult(
            entities=[Entity(name="AuthService", entity_type="Service")],
            relationships=[],
        ),
        llm_response="Auth token validation uses AuthService",
    )

    app.state.retriever = retriever
    app.state.settings = MagicMock()
    app.state.settings.APP_NAME = "test"

    if llm_available:
        llm = MagicMock()
        llm.generate.return_value = "{}"
        app.state.llm = llm
    else:
        app.state.llm = None

    app.include_router(health.router)
    app.include_router(evaluation.router)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        status_code = 500
        if exc.code in ("evaluation_dependency_error",):
            status_code = 503
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    return app


class TestRunEvaluation:
    """Tests for POST /api/v1/evaluation/run."""

    def test_run_evaluation_returns_200(self) -> None:
        app = _create_eval_test_app(llm_available=True)
        client = TestClient(app)

        response = client.post(
            "/api/v1/evaluation/run",
            json={
                "retrieval_cases": [
                    {
                        "case_id": "r1",
                        "query": "How auth works?",
                        "expected_memory_ids": ["mem-auth-1"],
                        "top_k": 2,
                    }
                ],
                "groundedness_cases": [
                    {
                        "case_id": "g1",
                        "query": "Explain auth",
                        "top_k": 2,
                        "entity_name": "AuthService",
                    }
                ],
                "agent_cases": [
                    {
                        "case_id": "a1",
                        "goal": "Build auth endpoint",
                        "required_terms": [],
                        "max_iterations": 1,
                        "require_approval": False,
                    }
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "summary" in data
        assert "retrieval_scores" in data
        assert "groundedness_scores" in data
        assert "agent_scores" in data

    def test_requires_llm_for_agent_cases(self) -> None:
        app = _create_eval_test_app(llm_available=False)
        client = TestClient(app)

        response = client.post(
            "/api/v1/evaluation/run",
            json={
                "agent_cases": [
                    {
                        "case_id": "a1",
                        "goal": "Build auth endpoint",
                        "required_terms": [],
                        "max_iterations": 1,
                        "require_approval": True,
                    }
                ]
            },
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "evaluation_dependency_error"
