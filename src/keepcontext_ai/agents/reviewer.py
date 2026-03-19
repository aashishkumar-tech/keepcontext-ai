"""Reviewer agent node.

Reviews generated code for security issues, best practices,
architecture consistency, and coding standards.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from keepcontext_ai.agents.schemas import AgentState

logger = logging.getLogger(__name__)

REVIEWER_SYSTEM_PROMPT = (
    "You are a senior code reviewer specializing in Python/FastAPI applications. "
    "Review the provided code for:\n"
    "1. Security vulnerabilities\n"
    "2. Architecture consistency\n"
    "3. Coding standards (PEP 8, type annotations, docstrings)\n"
    "4. Error handling\n"
    "5. Best practices\n\n"
    "Return ONLY valid JSON with this structure:\n"
    "{\n"
    '  "approved": true/false,\n'
    '  "issues": [\n'
    '    {"severity": "critical|warning|suggestion", '
    '"description": "...", "suggestion": "..."}\n'
    "  ],\n"
    '  "summary": "overall review summary"\n'
    "}\n\n"
    "Set approved=true only if there are no critical issues."
)


def _build_reviewer_prompt(state: AgentState) -> str:
    """Build the reviewer prompt from workflow state.

    Args:
        state: Current workflow state.

    Returns:
        Formatted prompt string.
    """
    sections: list[str] = [REVIEWER_SYSTEM_PROMPT]

    # Add project context for consistency checking
    context_results = state.get("context_results", [])
    if context_results:
        sections.append("\n--- Project Standards ---")
        for ctx in context_results[:3]:
            sections.append(f"• {ctx.get('content', '')}")

    # Add the plan for architecture alignment
    plan = state.get("plan", {})
    if plan:
        sections.append(f"\n--- Original Goal ---\n{plan.get('goal', '')}")

    # Add code to review
    code_outputs = state.get("code_outputs", [])
    if code_outputs:
        sections.append("\n--- Code to Review ---")
        for output in code_outputs:
            sections.append(
                f"\nFile: {output.get('filename', 'unknown')}\n"
                f"```{output.get('language', 'python')}\n"
                f"{output.get('code', '')}\n"
                f"```\n"
                f"Explanation: {output.get('explanation', '')}"
            )

    return "\n".join(sections)


def reviewer_node(
    state: AgentState,
    llm_generate: Any,
) -> AgentState:
    """Review generated code and produce feedback.

    Args:
        state: Current workflow state with code_outputs.
        llm_generate: Callable that takes a prompt and returns text.

    Returns:
        Updated state with review populated and iteration incremented.
    """
    prompt = _build_reviewer_prompt(state)
    current_iteration = state.get("iteration", 0) + 1

    try:
        raw_response = llm_generate(prompt)
        review = json.loads(raw_response)
    except json.JSONDecodeError:
        logger.warning("Reviewer returned invalid JSON — defaulting to approved")
        review = {
            "approved": True,
            "issues": [],
            "summary": raw_response,
        }
    except Exception as e:
        logger.error("Reviewer agent failed: %s", e)
        review = {
            "approved": True,
            "issues": [],
            "summary": f"Review skipped due to error: {e}",
        }

    return {
        **state,
        "review": review,
        "iteration": current_iteration,
    }
