"""Unit tests for the LangGraph agent workflow."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from keepcontext_ai.agents.schemas import AgentState
from keepcontext_ai.agents.workflow import (
    _assemble_response,
    _should_continue,
    build_workflow,
)
from keepcontext_ai.context.schemas import EnrichedContextResult
from keepcontext_ai.graph.schemas import GraphResult

# ---------------------------------------------------------------------------
# _should_continue
# ---------------------------------------------------------------------------


class TestShouldContinue:
    """Tests for the conditional edge function."""

    def test_approved_returns_end(self) -> None:
        state: AgentState = {
            "review": {"approved": True, "issues": [], "summary": "ok"},
            "iteration": 1,
            "max_iterations": 3,
        }  # type: ignore[typeddict-item]
        assert _should_continue(state) == "end"

    def test_rejected_under_max_returns_developer(self) -> None:
        state: AgentState = {
            "review": {"approved": False, "issues": [], "summary": "bad"},
            "iteration": 1,
            "max_iterations": 3,
        }  # type: ignore[typeddict-item]
        assert _should_continue(state) == "developer"

    def test_rejected_at_max_returns_end(self) -> None:
        state: AgentState = {
            "review": {"approved": False, "issues": [], "summary": "bad"},
            "iteration": 3,
            "max_iterations": 3,
        }  # type: ignore[typeddict-item]
        assert _should_continue(state) == "end"

    def test_no_review_returns_end(self) -> None:
        state: AgentState = {"iteration": 1, "max_iterations": 3}  # type: ignore[typeddict-item]
        assert _should_continue(state) == "end"

    def test_rejected_above_max_returns_end(self) -> None:
        state: AgentState = {
            "review": {"approved": False, "issues": [], "summary": "bad"},
            "iteration": 5,
            "max_iterations": 3,
        }  # type: ignore[typeddict-item]
        assert _should_continue(state) == "end"


# ---------------------------------------------------------------------------
# _assemble_response
# ---------------------------------------------------------------------------


class TestAssembleResponse:
    """Tests for the response assembler node."""

    def test_assembles_plan(self) -> None:
        state: AgentState = {
            "plan": {
                "goal": "Build API",
                "steps": [{"step_number": 1, "description": "Create routes"}],
                "architecture_notes": "FastAPI",
            },
        }  # type: ignore[typeddict-item]
        result = _assemble_response(state)
        assert "Build API" in result["final_response"]
        assert "Create routes" in result["final_response"]

    def test_assembles_code(self) -> None:
        state: AgentState = {
            "code_outputs": [
                {
                    "filename": "main.py",
                    "language": "python",
                    "code": "print('hi')",
                    "explanation": "entry point",
                }
            ],
        }  # type: ignore[typeddict-item]
        result = _assemble_response(state)
        assert "main.py" in result["final_response"]
        assert "print('hi')" in result["final_response"]

    def test_assembles_review(self) -> None:
        state: AgentState = {
            "review": {
                "approved": True,
                "issues": [],
                "summary": "All good",
            },
        }  # type: ignore[typeddict-item]
        result = _assemble_response(state)
        assert "✅ Approved" in result["final_response"]

    def test_assembles_error(self) -> None:
        state: AgentState = {"error": "Something broke"}  # type: ignore[typeddict-item]
        result = _assemble_response(state)
        assert "Something broke" in result["final_response"]

    def test_empty_state(self) -> None:
        state: AgentState = {}  # type: ignore[typeddict-item]
        result = _assemble_response(state)
        assert "final_response" in result


# ---------------------------------------------------------------------------
# build_workflow (integration-style unit test with mocked LLM)
# ---------------------------------------------------------------------------


class TestBuildWorkflow:
    """Tests for the compiled workflow graph."""

    def _mock_retriever(self) -> MagicMock:
        mock = MagicMock()
        enriched = EnrichedContextResult(
            memory_results=[],
            graph_context=GraphResult(),
            llm_response=None,
        )
        mock.query_enriched.return_value = enriched
        return mock

    def _mock_llm(self, responses: list[str]) -> MagicMock:
        """Return a callable that yields successive responses."""
        mock = MagicMock()
        mock.side_effect = responses
        return mock

    def test_full_workflow_approved_first_try(self) -> None:
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
                    "explanation": "Entry",
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

        retriever = self._mock_retriever()
        llm = self._mock_llm([plan, code, review])

        workflow = build_workflow(retriever=retriever, llm_generate=llm)
        result = workflow.invoke(
            {
                "goal": "Build API",
                "max_iterations": 3,
                "iteration": 0,
            }
        )

        assert result.get("final_response")
        assert "Build API" in result["final_response"]
        assert result["review"]["approved"] is True

    def test_workflow_loops_on_rejection(self) -> None:
        plan = json.dumps(
            {
                "goal": "task",
                "steps": [{"step_number": 1, "description": "Do it", "details": ""}],
                "architecture_notes": "",
            }
        )
        code_v1 = json.dumps(
            [
                {
                    "filename": "a.py",
                    "language": "python",
                    "code": "v1",
                    "explanation": "",
                }
            ]
        )
        review_reject = json.dumps(
            {
                "approved": False,
                "issues": [
                    {
                        "severity": "critical",
                        "description": "bug",
                        "suggestion": "fix it",
                    }
                ],
                "summary": "Needs work",
            }
        )
        code_v2 = json.dumps(
            [
                {
                    "filename": "a.py",
                    "language": "python",
                    "code": "v2",
                    "explanation": "",
                }
            ]
        )
        review_approve = json.dumps(
            {
                "approved": True,
                "issues": [],
                "summary": "Fixed",
            }
        )

        retriever = self._mock_retriever()
        llm = self._mock_llm([plan, code_v1, review_reject, code_v2, review_approve])

        workflow = build_workflow(retriever=retriever, llm_generate=llm)
        result = workflow.invoke(
            {
                "goal": "task",
                "max_iterations": 3,
                "iteration": 0,
            }
        )

        assert result["review"]["approved"] is True
        assert result["iteration"] == 2  # Two review passes

    def test_workflow_stops_at_max_iterations(self) -> None:
        plan = json.dumps(
            {
                "goal": "task",
                "steps": [],
                "architecture_notes": "",
            }
        )
        code = json.dumps(
            [
                {
                    "filename": "a.py",
                    "language": "python",
                    "code": "bad code",
                    "explanation": "",
                }
            ]
        )
        reject = json.dumps(
            {
                "approved": False,
                "issues": [
                    {"severity": "critical", "description": "bug", "suggestion": "fix"}
                ],
                "summary": "Still bad",
            }
        )

        # With max_iterations=1: planner(1) + developer(1) + reviewer(1) → rejected, iteration=1 >= max → end
        retriever = self._mock_retriever()
        llm = self._mock_llm([plan, code, reject])

        workflow = build_workflow(retriever=retriever, llm_generate=llm)
        result = workflow.invoke(
            {
                "goal": "task",
                "max_iterations": 1,
                "iteration": 0,
            }
        )

        assert result["review"]["approved"] is False
        assert "final_response" in result
