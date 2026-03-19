"""Agent workflow endpoints.

Exposes the LangGraph multi-agent pipeline (plan → develop → review)
via REST endpoints.

Endpoints:
    POST /api/v1/agents/run     — Run the full agent workflow.
    POST /api/v1/agents/plan    — Run context + planner only.
    POST /api/v1/agents/review  — Run reviewer on provided code.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from keepcontext_ai.agents.schemas import AgentRequest, AgentResponse, AgentState
from keepcontext_ai.agents.workflow import build_workflow
from keepcontext_ai.exceptions import AgentError

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_llm_generate(request: Request) -> Any:
    """Return the Groq LLM generate callable from app state.

    Raises:
        AgentError: If the LLM service is unavailable.
    """
    llm = getattr(request.app.state, "llm", None)
    if llm is None:
        raise AgentError(message="LLM service unavailable", code="agent_error")
    return llm.generate


# ---------------------------------------------------------------------------
# POST /api/v1/agents/run — Full workflow
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_agent_workflow(
    request: Request,
    body: AgentRequest,
) -> dict[str, Any]:
    """Execute the full agent workflow.

    Flow: context_manager → planner → developer → reviewer (loop) → assembler.

    Args:
        request: The FastAPI request.
        body: Agent request with goal and options.

    Returns:
        AgentResponse dict with plan, code, review, and final response.
    """
    retriever = request.app.state.retriever
    llm_generate = _get_llm_generate(request)

    workflow = build_workflow(retriever=retriever, llm_generate=llm_generate)

    initial_state: AgentState = {
        "goal": body.goal,
        "max_iterations": body.max_iterations,
        "iteration": 0,
    }

    result = workflow.invoke(initial_state)

    return AgentResponse(
        goal=body.goal,
        plan=result.get("plan"),
        code_outputs=result.get("code_outputs", []),
        review=result.get("review"),
        final_response=result.get("final_response", ""),
        iterations_used=result.get("iteration", 1),
    ).model_dump()


# ---------------------------------------------------------------------------
# POST /api/v1/agents/plan — Planner only
# ---------------------------------------------------------------------------


class PlanRequest(BaseModel):
    """Request model for the plan-only endpoint."""

    model_config = ConfigDict(frozen=True)

    goal: str = Field(..., min_length=1, max_length=5000)
    entity_name: str | None = Field(default=None)


@router.post("/plan")
async def plan_only(
    request: Request,
    body: PlanRequest,
) -> dict[str, Any]:
    """Run context retrieval + planner only (no code generation).

    Args:
        request: The FastAPI request.
        body: Plan request with goal.

    Returns:
        Dict with plan and context used.
    """
    from keepcontext_ai.agents.context_manager import context_manager_node
    from keepcontext_ai.agents.planner import planner_node

    retriever = request.app.state.retriever
    llm_generate = _get_llm_generate(request)

    state: AgentState = {"goal": body.goal}
    state = context_manager_node(state, retriever=retriever)
    state = planner_node(state, llm_generate=llm_generate)

    return {
        "goal": body.goal,
        "plan": state.get("plan", {}),
        "context_used": len(state.get("context_results", [])),
    }


# ---------------------------------------------------------------------------
# POST /api/v1/agents/review — Review provided code
# ---------------------------------------------------------------------------


class ReviewRequest(BaseModel):
    """Request model for the review-only endpoint."""

    model_config = ConfigDict(frozen=True)

    goal: str = Field(..., min_length=1, max_length=5000)
    code_outputs: list[dict[str, Any]] = Field(..., min_length=1)


@router.post("/review")
async def review_only(
    request: Request,
    body: ReviewRequest,
) -> dict[str, Any]:
    """Run the reviewer agent on provided code outputs.

    Args:
        request: The FastAPI request.
        body: Review request with goal and code_outputs.

    Returns:
        Dict with review results.
    """
    from keepcontext_ai.agents.reviewer import reviewer_node

    llm_generate = _get_llm_generate(request)

    state: AgentState = {
        "goal": body.goal,
        "code_outputs": body.code_outputs,
        "iteration": 0,
    }
    state = reviewer_node(state, llm_generate=llm_generate)

    return {
        "goal": body.goal,
        "review": state.get("review", {}),
    }
