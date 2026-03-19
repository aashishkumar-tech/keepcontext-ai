"""Unit tests for agent schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from keepcontext_ai.agents.schemas import (
    AgentRequest,
    AgentResponse,
    AgentState,
    CodeOutput,
    ReviewIssue,
    ReviewResult,
    TaskPlan,
    TaskStep,
)

# ---------------------------------------------------------------------------
# AgentRequest
# ---------------------------------------------------------------------------


class TestAgentRequest:
    """Tests for AgentRequest validation."""

    def test_valid_request(self) -> None:
        req = AgentRequest(goal="Build a REST API")
        assert req.goal == "Build a REST API"
        assert req.max_iterations == 3
        assert req.entity_name is None

    def test_with_entity_name(self) -> None:
        req = AgentRequest(goal="Refactor auth", entity_name="AuthService")
        assert req.entity_name == "AuthService"

    def test_custom_max_iterations(self) -> None:
        req = AgentRequest(goal="task", max_iterations=7)
        assert req.max_iterations == 7

    def test_empty_goal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentRequest(goal="")

    def test_max_iterations_bounds(self) -> None:
        with pytest.raises(ValidationError):
            AgentRequest(goal="task", max_iterations=0)
        with pytest.raises(ValidationError):
            AgentRequest(goal="task", max_iterations=11)

    def test_frozen(self) -> None:
        req = AgentRequest(goal="task")
        with pytest.raises(ValidationError):
            req.goal = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TaskStep / TaskPlan
# ---------------------------------------------------------------------------


class TestTaskStep:
    """Tests for TaskStep model."""

    def test_valid_step(self) -> None:
        step = TaskStep(step_number=1, description="Install deps")
        assert step.step_number == 1
        assert step.details == ""

    def test_with_details(self) -> None:
        step = TaskStep(step_number=2, description="Write tests", details="pytest")
        assert step.details == "pytest"


class TestTaskPlan:
    """Tests for TaskPlan model."""

    def test_valid_plan(self) -> None:
        plan = TaskPlan(
            goal="Build API",
            steps=[TaskStep(step_number=1, description="Create routes")],
            architecture_notes="Use FastAPI",
        )
        assert plan.goal == "Build API"
        assert len(plan.steps) == 1

    def test_empty_steps(self) -> None:
        plan = TaskPlan(goal="Empty plan")
        assert plan.steps == []
        assert plan.architecture_notes == ""


# ---------------------------------------------------------------------------
# CodeOutput
# ---------------------------------------------------------------------------


class TestCodeOutput:
    """Tests for CodeOutput model."""

    def test_valid_output(self) -> None:
        out = CodeOutput(filename="main.py", code="print('hello')")
        assert out.language == "python"
        assert out.explanation == ""

    def test_custom_language(self) -> None:
        out = CodeOutput(filename="app.ts", language="typescript", code="const x = 1;")
        assert out.language == "typescript"


# ---------------------------------------------------------------------------
# ReviewIssue / ReviewResult
# ---------------------------------------------------------------------------


class TestReviewIssue:
    """Tests for ReviewIssue model."""

    def test_valid_severities(self) -> None:
        for sev in ("critical", "warning", "suggestion"):
            issue = ReviewIssue(severity=sev, description="test")
            assert issue.severity == sev

    def test_invalid_severity(self) -> None:
        with pytest.raises(ValidationError):
            ReviewIssue(severity="info", description="test")


class TestReviewResult:
    """Tests for ReviewResult model."""

    def test_approved(self) -> None:
        result = ReviewResult(approved=True, summary="Looks good")
        assert result.approved is True
        assert result.issues == []

    def test_rejected_with_issues(self) -> None:
        result = ReviewResult(
            approved=False,
            issues=[
                ReviewIssue(
                    severity="critical",
                    description="SQL injection",
                    suggestion="Use parameterised queries",
                )
            ],
            summary="Security issue found",
        )
        assert result.approved is False
        assert len(result.issues) == 1


# ---------------------------------------------------------------------------
# AgentResponse
# ---------------------------------------------------------------------------


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_minimal(self) -> None:
        resp = AgentResponse(goal="task")
        assert resp.plan is None
        assert resp.code_outputs == []
        assert resp.iterations_used == 1

    def test_full(self) -> None:
        resp = AgentResponse(
            goal="task",
            plan=TaskPlan(goal="task"),
            code_outputs=[CodeOutput(filename="a.py", code="pass")],
            review=ReviewResult(approved=True, summary="ok"),
            final_response="Done",
            iterations_used=2,
        )
        assert resp.iterations_used == 2
        assert resp.final_response == "Done"


# ---------------------------------------------------------------------------
# AgentState TypedDict
# ---------------------------------------------------------------------------


class TestAgentState:
    """Tests for AgentState TypedDict (runtime dict usage)."""

    def test_create_state(self) -> None:
        state: AgentState = {"goal": "Build feature"}  # type: ignore[typeddict-item]
        assert state["goal"] == "Build feature"

    def test_optional_fields(self) -> None:
        state: AgentState = {}  # type: ignore[typeddict-item]
        assert state.get("plan") is None
        assert state.get("iteration") is None
