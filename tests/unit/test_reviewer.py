"""Unit tests for the reviewer agent node."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from keepcontext_ai.agents.reviewer import (
    REVIEWER_SYSTEM_PROMPT,
    _build_reviewer_prompt,
    reviewer_node,
)
from keepcontext_ai.agents.schemas import AgentState

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


class TestBuildReviewerPrompt:
    """Tests for _build_reviewer_prompt."""

    def test_includes_system_prompt(self) -> None:
        state: AgentState = {"goal": "Review code"}  # type: ignore[typeddict-item]
        prompt = _build_reviewer_prompt(state)
        assert REVIEWER_SYSTEM_PROMPT in prompt

    def test_includes_code_outputs(self) -> None:
        state: AgentState = {
            "goal": "task",
            "code_outputs": [
                {
                    "filename": "app.py",
                    "language": "python",
                    "code": "print('hello')",
                    "explanation": "Main entry",
                }
            ],
        }  # type: ignore[typeddict-item]
        prompt = _build_reviewer_prompt(state)
        assert "app.py" in prompt
        assert "print('hello')" in prompt

    def test_includes_plan_goal(self) -> None:
        state: AgentState = {
            "goal": "task",
            "plan": {"goal": "Build API"},
        }  # type: ignore[typeddict-item]
        prompt = _build_reviewer_prompt(state)
        assert "Build API" in prompt

    def test_includes_context(self) -> None:
        state: AgentState = {
            "goal": "task",
            "context_results": [
                {"content": "Use JWT auth", "memory_type": "decision", "score": 0.9}
            ],
        }  # type: ignore[typeddict-item]
        prompt = _build_reviewer_prompt(state)
        assert "Use JWT auth" in prompt


# ---------------------------------------------------------------------------
# Reviewer node
# ---------------------------------------------------------------------------


class TestReviewerNode:
    """Tests for reviewer_node."""

    def test_approved_response(self) -> None:
        review = {
            "approved": True,
            "issues": [],
            "summary": "Code looks good",
        }
        llm = MagicMock(return_value=json.dumps(review))

        state: AgentState = {"goal": "task", "iteration": 0}  # type: ignore[typeddict-item]
        result = reviewer_node(state, llm_generate=llm)

        assert result["review"]["approved"] is True
        assert result["iteration"] == 1

    def test_rejected_response(self) -> None:
        review = {
            "approved": False,
            "issues": [
                {
                    "severity": "critical",
                    "description": "SQL injection",
                    "suggestion": "Use parameterised queries",
                }
            ],
            "summary": "Security issue",
        }
        llm = MagicMock(return_value=json.dumps(review))

        state: AgentState = {"goal": "task", "iteration": 0}  # type: ignore[typeddict-item]
        result = reviewer_node(state, llm_generate=llm)

        assert result["review"]["approved"] is False
        assert len(result["review"]["issues"]) == 1
        assert result["iteration"] == 1

    def test_invalid_json_defaults_approved(self) -> None:
        llm = MagicMock(return_value="The code looks fine to me!")

        state: AgentState = {"goal": "task", "iteration": 0}  # type: ignore[typeddict-item]
        result = reviewer_node(state, llm_generate=llm)

        assert result["review"]["approved"] is True
        assert "The code looks fine" in result["review"]["summary"]

    def test_llm_exception_defaults_approved(self) -> None:
        llm = MagicMock(side_effect=RuntimeError("LLM crashed"))

        state: AgentState = {"goal": "task", "iteration": 0}  # type: ignore[typeddict-item]
        result = reviewer_node(state, llm_generate=llm)

        assert result["review"]["approved"] is True
        assert "error" in result["review"]["summary"].lower()

    def test_increments_iteration(self) -> None:
        llm = MagicMock(return_value='{"approved":true,"issues":[],"summary":"ok"}')

        state: AgentState = {"goal": "task", "iteration": 2}  # type: ignore[typeddict-item]
        result = reviewer_node(state, llm_generate=llm)

        assert result["iteration"] == 3

    def test_preserves_state(self) -> None:
        llm = MagicMock(return_value='{"approved":true,"issues":[],"summary":"ok"}')

        state: AgentState = {
            "goal": "task",
            "iteration": 0,
            "code_outputs": [{"filename": "a.py"}],
        }  # type: ignore[typeddict-item]
        result = reviewer_node(state, llm_generate=llm)

        assert result["code_outputs"] == [{"filename": "a.py"}]
