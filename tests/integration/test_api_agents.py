"""Integration tests for agent API endpoints."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from keepcontext_ai.context.schemas import EnrichedContextResult
from keepcontext_ai.graph.schemas import GraphResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _create_agent_test_app(
    llm_responses: list[str] | None = None,
    llm_available: bool = True,
) -> FastAPI:
    """Build a FastAPI test app with mocked services for agent tests."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    from keepcontext_ai.api.routes import agents, health
    from keepcontext_ai.exceptions import AppError

    app = FastAPI(title="test-agents")

    # Mock retriever
    retriever = MagicMock()
    enriched = EnrichedContextResult(
        memory_results=[],
        graph_context=GraphResult(),
        llm_response=None,
    )
    retriever.query_enriched.return_value = enriched

    # Mock LLM
    if llm_available:
        llm_mock = MagicMock()
        if llm_responses:
            llm_mock.generate.side_effect = llm_responses
        else:
            llm_mock.generate.return_value = (
                '{"approved":true,"issues":[],"summary":"ok"}'
            )
        app.state.llm = llm_mock
    else:
        app.state.llm = None

    app.state.retriever = retriever
    app.state.settings = MagicMock()
    app.state.settings.APP_NAME = "test"

    app.include_router(health.router)
    app.include_router(agents.router)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        status_code = 500
        if exc.code in ("agent_error",):
            status_code = 503
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    return app


# ---------------------------------------------------------------------------
# POST /api/v1/agents/run
# ---------------------------------------------------------------------------


class TestRunAgentWorkflow:
    """Tests for the full agent workflow endpoint."""

    def test_successful_run(self) -> None:
        plan = json.dumps(
            {
                "goal": "Build API",
                "steps": [
                    {"step_number": 1, "description": "Create routes", "details": ""}
                ],
                "architecture_notes": "",
            }
        )
        code = json.dumps(
            [
                {
                    "filename": "app.py",
                    "language": "python",
                    "code": "print('hello')",
                    "explanation": "Main entry",
                }
            ]
        )
        review = json.dumps(
            {
                "approved": True,
                "issues": [],
                "summary": "Looks good",
            }
        )

        app = _create_agent_test_app(llm_responses=[plan, code, review])
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/run",
            json={"goal": "Build API", "max_iterations": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["goal"] == "Build API"
        assert data["final_response"]

    def test_llm_unavailable(self) -> None:
        app = _create_agent_test_app(llm_available=False)
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/run",
            json={"goal": "Build API"},
        )

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "agent_error"

    def test_empty_goal_rejected(self) -> None:
        app = _create_agent_test_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/run",
            json={"goal": ""},
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/agents/plan
# ---------------------------------------------------------------------------


class TestPlanOnly:
    """Tests for the plan-only endpoint."""

    def test_successful_plan(self) -> None:
        plan = json.dumps(
            {
                "goal": "Add caching",
                "steps": [
                    {"step_number": 1, "description": "Set up Redis", "details": ""}
                ],
                "architecture_notes": "Use Redis",
            }
        )

        app = _create_agent_test_app(llm_responses=[plan])
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/plan",
            json={"goal": "Add caching"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["goal"] == "Add caching"
        assert "plan" in data

    def test_llm_unavailable(self) -> None:
        app = _create_agent_test_app(llm_available=False)
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/plan",
            json={"goal": "Add caching"},
        )

        assert response.status_code == 503


# ---------------------------------------------------------------------------
# POST /api/v1/agents/review
# ---------------------------------------------------------------------------


class TestReviewOnly:
    """Tests for the review-only endpoint."""

    def test_successful_review(self) -> None:
        review = json.dumps(
            {
                "approved": True,
                "issues": [],
                "summary": "Code looks great",
            }
        )

        app = _create_agent_test_app(llm_responses=[review])
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/review",
            json={
                "goal": "Review my code",
                "code_outputs": [
                    {
                        "filename": "app.py",
                        "language": "python",
                        "code": "print('hello')",
                        "explanation": "test",
                    }
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["review"]["approved"] is True

    def test_llm_unavailable(self) -> None:
        app = _create_agent_test_app(llm_available=False)
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/review",
            json={
                "goal": "Review",
                "code_outputs": [{"filename": "a.py", "code": "pass"}],
            },
        )

        assert response.status_code == 503

    def test_empty_code_outputs_rejected(self) -> None:
        app = _create_agent_test_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/agents/review",
            json={"goal": "Review", "code_outputs": []},
        )

        assert response.status_code == 422
