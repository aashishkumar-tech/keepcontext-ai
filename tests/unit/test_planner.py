"""Unit tests for the planner agent node."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from keepcontext_ai.agents.planner import (
    PLANNER_SYSTEM_PROMPT,
    _build_planner_prompt,
    planner_node,
)
from keepcontext_ai.agents.schemas import AgentState

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


class TestBuildPlannerPrompt:
    """Tests for _build_planner_prompt."""

    def test_includes_system_prompt(self) -> None:
        state: AgentState = {"goal": "Build auth"}  # type: ignore[typeddict-item]
        prompt = _build_planner_prompt(state)
        assert PLANNER_SYSTEM_PROMPT in prompt

    def test_includes_goal(self) -> None:
        state: AgentState = {"goal": "Implement caching"}  # type: ignore[typeddict-item]
        prompt = _build_planner_prompt(state)
        assert "Implement caching" in prompt

    def test_includes_context(self) -> None:
        state: AgentState = {
            "goal": "task",
            "context_results": [
                {"content": "Uses Redis", "memory_type": "decision", "score": 0.9}
            ],
        }  # type: ignore[typeddict-item]
        prompt = _build_planner_prompt(state)
        assert "Uses Redis" in prompt

    def test_includes_graph_relationships(self) -> None:
        state: AgentState = {
            "goal": "task",
            "graph_context": {
                "entities": [],
                "relationships": [
                    {
                        "source": "UserService",
                        "relationship_type": "DEPENDS_ON",
                        "target": "Database",
                    }
                ],
            },
        }  # type: ignore[typeddict-item]
        prompt = _build_planner_prompt(state)
        assert "UserService" in prompt
        assert "DEPENDS_ON" in prompt


# ---------------------------------------------------------------------------
# Planner node
# ---------------------------------------------------------------------------


class TestPlannerNode:
    """Tests for planner_node."""

    def test_valid_json_response(self) -> None:
        plan_dict = {
            "goal": "Build API",
            "steps": [
                {"step_number": 1, "description": "Create models", "details": ""}
            ],
            "architecture_notes": "Use FastAPI",
        }
        llm = MagicMock(return_value=json.dumps(plan_dict))

        state: AgentState = {"goal": "Build API"}  # type: ignore[typeddict-item]
        result = planner_node(state, llm_generate=llm)

        assert result["plan"] == plan_dict
        assert "error" not in result

    def test_invalid_json_fallback(self) -> None:
        llm = MagicMock(return_value="Here is a rough plan: do X then Y")

        state: AgentState = {"goal": "Build API"}  # type: ignore[typeddict-item]
        result = planner_node(state, llm_generate=llm)

        assert result["plan"]["goal"] == "Build API"
        assert len(result["plan"]["steps"]) == 1
        assert "Here is a rough plan" in result["plan"]["steps"][0]["description"]

    def test_llm_exception_handled(self) -> None:
        llm = MagicMock(side_effect=RuntimeError("LLM down"))

        state: AgentState = {"goal": "Build API"}  # type: ignore[typeddict-item]
        result = planner_node(state, llm_generate=llm)

        assert result["plan"]["steps"] == []
        assert "Planner failed" in result.get("error", "")

    def test_preserves_state(self) -> None:
        llm = MagicMock(return_value='{"goal":"x","steps":[],"architecture_notes":""}')

        state: AgentState = {
            "goal": "x",
            "context_results": [{"content": "data"}],
        }  # type: ignore[typeddict-item]
        result = planner_node(state, llm_generate=llm)

        assert result["context_results"] == [{"content": "data"}]
