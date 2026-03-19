"""Unit tests for the developer agent node."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from keepcontext_ai.agents.developer import (
    DEVELOPER_SYSTEM_PROMPT,
    _build_developer_prompt,
    developer_node,
)
from keepcontext_ai.agents.schemas import AgentState

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


class TestBuildDeveloperPrompt:
    """Tests for _build_developer_prompt."""

    def test_includes_system_prompt(self) -> None:
        state: AgentState = {"goal": "Build auth"}  # type: ignore[typeddict-item]
        prompt = _build_developer_prompt(state)
        assert DEVELOPER_SYSTEM_PROMPT in prompt

    def test_includes_plan(self) -> None:
        state: AgentState = {
            "goal": "task",
            "plan": {
                "goal": "task",
                "steps": [{"step_number": 1, "description": "Create endpoint"}],
                "architecture_notes": "FastAPI",
            },
        }  # type: ignore[typeddict-item]
        prompt = _build_developer_prompt(state)
        assert "Create endpoint" in prompt
        assert "FastAPI" in prompt

    def test_includes_review_feedback_when_rejected(self) -> None:
        state: AgentState = {
            "goal": "task",
            "review": {
                "approved": False,
                "issues": [
                    {
                        "severity": "critical",
                        "description": "Missing error handling",
                        "suggestion": "Add try/except",
                    }
                ],
                "summary": "Needs work",
            },
        }  # type: ignore[typeddict-item]
        prompt = _build_developer_prompt(state)
        assert "Missing error handling" in prompt
        assert "Add try/except" in prompt

    def test_skips_review_when_approved(self) -> None:
        state: AgentState = {
            "goal": "task",
            "review": {"approved": True, "issues": [], "summary": "Good"},
        }  # type: ignore[typeddict-item]
        prompt = _build_developer_prompt(state)
        assert "Reviewer Feedback" not in prompt


# ---------------------------------------------------------------------------
# Developer node
# ---------------------------------------------------------------------------


class TestDeveloperNode:
    """Tests for developer_node."""

    def test_valid_json_array_response(self) -> None:
        outputs = [
            {
                "filename": "app.py",
                "language": "python",
                "code": "print('hello')",
                "explanation": "Main entry",
            }
        ]
        llm = MagicMock(return_value=json.dumps(outputs))

        state: AgentState = {"goal": "Build app"}  # type: ignore[typeddict-item]
        result = developer_node(state, llm_generate=llm)

        assert len(result["code_outputs"]) == 1
        assert result["code_outputs"][0]["filename"] == "app.py"

    def test_single_object_wrapped_in_list(self) -> None:
        output = {
            "filename": "app.py",
            "language": "python",
            "code": "pass",
            "explanation": "",
        }
        llm = MagicMock(return_value=json.dumps(output))

        state: AgentState = {"goal": "task"}  # type: ignore[typeddict-item]
        result = developer_node(state, llm_generate=llm)

        assert isinstance(result["code_outputs"], list)
        assert len(result["code_outputs"]) == 1

    def test_invalid_json_fallback(self) -> None:
        llm = MagicMock(return_value="def hello():\n    pass")

        state: AgentState = {"goal": "task"}  # type: ignore[typeddict-item]
        result = developer_node(state, llm_generate=llm)

        assert len(result["code_outputs"]) == 1
        assert result["code_outputs"][0]["filename"] == "implementation.py"
        assert "def hello" in result["code_outputs"][0]["code"]

    def test_llm_exception_handled(self) -> None:
        llm = MagicMock(side_effect=RuntimeError("LLM crashed"))

        state: AgentState = {"goal": "task"}  # type: ignore[typeddict-item]
        result = developer_node(state, llm_generate=llm)

        assert result["code_outputs"] == []
        assert "Developer failed" in result.get("error", "")

    def test_preserves_state(self) -> None:
        llm = MagicMock(
            return_value='[{"filename":"a.py","language":"python","code":"x","explanation":""}]'
        )

        state: AgentState = {"goal": "task", "plan": {"goal": "task"}}  # type: ignore[typeddict-item]
        result = developer_node(state, llm_generate=llm)

        assert result["plan"] == {"goal": "task"}
