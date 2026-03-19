"""Planner agent node.

Converts a developer goal into a structured task plan
using project context and LLM inference.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from keepcontext_ai.agents.schemas import AgentState

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = (
    "You are a senior software architect and project planner. "
    "Given a developer's goal and relevant project context, create a structured "
    "development plan.\n\n"
    "Return ONLY valid JSON with this structure:\n"
    "{\n"
    '  "goal": "the original goal",\n'
    '  "steps": [\n'
    '    {"step_number": 1, "description": "...", "details": "..."},\n'
    '    {"step_number": 2, "description": "...", "details": "..."}\n'
    "  ],\n"
    '  "architecture_notes": "any relevant architecture observations"\n'
    "}\n\n"
    "Be specific and actionable. Each step should be a concrete task."
)


def _build_planner_prompt(state: AgentState) -> str:
    """Build the planner prompt from workflow state.

    Args:
        state: Current workflow state.

    Returns:
        Formatted prompt string.
    """
    sections: list[str] = [PLANNER_SYSTEM_PROMPT]

    # Add project context
    context_results = state.get("context_results", [])
    if context_results:
        sections.append("\n--- Relevant Project Knowledge ---")
        for i, ctx in enumerate(context_results, 1):
            sections.append(
                f"{i}. [{ctx.get('memory_type', 'unknown')}] "
                f"(relevance: {ctx.get('score', 0):.2f}): "
                f"{ctx.get('content', '')}"
            )

    # Add graph context
    graph_context = state.get("graph_context", {})
    relationships = graph_context.get("relationships", [])
    if relationships:
        sections.append("\n--- Architecture Relationships ---")
        for rel in relationships:
            sections.append(
                f"• {rel.get('source', '?')} "
                f"--[{rel.get('relationship_type', '?')}]--> "
                f"{rel.get('target', '?')}"
            )

    sections.append(f"\n--- Developer Goal ---\n{state.get('goal', '')}")

    return "\n".join(sections)


def planner_node(
    state: AgentState,
    llm_generate: Any,
) -> AgentState:
    """Generate a task plan from the developer's goal.

    Args:
        state: Current workflow state with goal and context.
        llm_generate: Callable that takes a prompt and returns text.

    Returns:
        Updated state with the plan populated.
    """
    prompt = _build_planner_prompt(state)

    try:
        raw_response = llm_generate(prompt)
        plan = json.loads(raw_response)
    except json.JSONDecodeError:
        logger.warning("Planner returned invalid JSON — using raw text")
        plan = {
            "goal": state.get("goal", ""),
            "steps": [{"step_number": 1, "description": raw_response, "details": ""}],
            "architecture_notes": "",
        }
    except Exception as e:
        logger.error("Planner agent failed: %s", e)
        return {
            **state,
            "plan": {
                "goal": state.get("goal", ""),
                "steps": [],
                "architecture_notes": "",
            },
            "error": f"Planner failed: {e}",
        }

    return {**state, "plan": plan}
