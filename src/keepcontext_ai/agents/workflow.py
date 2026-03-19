"""LangGraph agent workflow.

Wires Context Manager → Planner → Developer → Reviewer into a
cyclic StateGraph with a conditional review loop.
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from keepcontext_ai.agents.context_manager import context_manager_node
from keepcontext_ai.agents.developer import developer_node
from keepcontext_ai.agents.planner import planner_node
from keepcontext_ai.agents.reviewer import reviewer_node
from keepcontext_ai.agents.schemas import AgentState
from keepcontext_ai.context.retrieval import ContextRetriever

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conditional edge: decide whether to loop back to developer or finish
# ---------------------------------------------------------------------------


def _should_continue(state: AgentState) -> Literal["developer", "end"]:
    """Determine whether the workflow should loop or finish.

    Loops back to the developer node when the reviewer rejects the
    code AND the iteration count has not exceeded *max_iterations*.

    Args:
        state: Current workflow state.

    Returns:
        ``"developer"`` to re-generate, or ``"end"`` to finish.
    """
    review = state.get("review", {})
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)

    approved = review.get("approved", True)
    if not approved and iteration < max_iterations:
        logger.info(
            "Review rejected (iteration %d/%d) — looping back to developer",
            iteration,
            max_iterations,
        )
        return "developer"

    return "end"


# ---------------------------------------------------------------------------
# Assemble final response
# ---------------------------------------------------------------------------


def _assemble_response(state: AgentState) -> AgentState:
    """Build the final_response string from plan + code + review.

    Args:
        state: Completed workflow state.

    Returns:
        State with ``final_response`` populated.
    """
    parts: list[str] = []

    plan = state.get("plan", {})
    if plan:
        parts.append(f"## Plan\n**Goal:** {plan.get('goal', '')}")
        for step in plan.get("steps", []):
            parts.append(
                f"  {step.get('step_number', '?')}. {step.get('description', '')}"
            )
        notes = plan.get("architecture_notes", "")
        if notes:
            parts.append(f"\n**Architecture notes:** {notes}")

    code_outputs = state.get("code_outputs", [])
    if code_outputs:
        parts.append("\n## Generated Code")
        for output in code_outputs:
            parts.append(
                f"\n### {output.get('filename', 'file')}\n"
                f"```{output.get('language', 'python')}\n"
                f"{output.get('code', '')}\n"
                f"```\n"
                f"{output.get('explanation', '')}"
            )

    review = state.get("review", {})
    if review:
        status = "✅ Approved" if review.get("approved") else "❌ Needs revision"
        parts.append(f"\n## Review: {status}")
        parts.append(review.get("summary", ""))
        for issue in review.get("issues", []):
            parts.append(
                f"- [{issue.get('severity', '?')}] {issue.get('description', '')}"
            )

    error = state.get("error", "")
    if error:
        parts.append(f"\n⚠️ **Error:** {error}")

    return {**state, "final_response": "\n".join(parts)}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_workflow(
    retriever: ContextRetriever,
    llm_generate: Any,
) -> Any:
    """Construct and compile the LangGraph agent workflow.

    The graph follows this flow::

        START → context_manager → planner → developer → reviewer
                                                ↑          ↓
                                                └── (not approved & iterations left)
                                                           ↓
                                               assembler → END

    Args:
        retriever: Context retriever for memory + graph lookups.
        llm_generate: Callable ``(prompt: str) -> str`` for LLM inference.

    Returns:
        Compiled LangGraph ``StateGraph`` ready for invocation.
    """
    graph = StateGraph(AgentState)

    # Bind external dependencies via functools.partial
    context_node = functools.partial(context_manager_node, retriever=retriever)
    plan_node = functools.partial(planner_node, llm_generate=llm_generate)
    dev_node = functools.partial(developer_node, llm_generate=llm_generate)
    rev_node = functools.partial(reviewer_node, llm_generate=llm_generate)

    # Register nodes
    graph.add_node("context_manager", context_node)
    graph.add_node("planner", plan_node)
    graph.add_node("developer", dev_node)
    graph.add_node("reviewer", rev_node)
    graph.add_node("assembler", _assemble_response)

    # Edges
    graph.add_edge(START, "context_manager")
    graph.add_edge("context_manager", "planner")
    graph.add_edge("planner", "developer")
    graph.add_edge("developer", "reviewer")

    # Conditional edge after reviewer
    graph.add_conditional_edges(
        "reviewer",
        _should_continue,
        {
            "developer": "developer",
            "end": "assembler",
        },
    )

    graph.add_edge("assembler", END)

    return graph.compile()
