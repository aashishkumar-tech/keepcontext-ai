"""Developer agent node.

Generates code implementations based on the task plan
and project context.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from keepcontext_ai.agents.schemas import AgentState

logger = logging.getLogger(__name__)

DEVELOPER_SYSTEM_PROMPT = (
    "You are an expert software developer. Given a task plan and project context, "
    "generate clean, production-ready code implementations.\n\n"
    "Return ONLY valid JSON with this structure:\n"
    "[\n"
    "  {\n"
    '    "filename": "path/to/file.py",\n'
    '    "language": "python",\n'
    '    "code": "the source code",\n'
    '    "explanation": "what this code does"\n'
    "  }\n"
    "]\n\n"
    "Follow these rules:\n"
    "- Type annotations on all function signatures\n"
    "- Docstrings on all public functions/classes\n"
    "- Handle errors with try/except and custom exceptions\n"
    "- Use dependency injection\n"
    "- Keep functions under 50 lines\n"
    "- Follow PEP 8 conventions"
)


def _build_developer_prompt(state: AgentState) -> str:
    """Build the developer prompt from workflow state.

    Args:
        state: Current workflow state.

    Returns:
        Formatted prompt string.
    """
    sections: list[str] = [DEVELOPER_SYSTEM_PROMPT]

    # Add project context
    context_results = state.get("context_results", [])
    if context_results:
        sections.append("\n--- Relevant Project Knowledge ---")
        for i, ctx in enumerate(context_results[:3], 1):
            sections.append(
                f"{i}. [{ctx.get('memory_type', '')}]: {ctx.get('content', '')}"
            )

    # Add the plan
    plan = state.get("plan", {})
    if plan:
        sections.append("\n--- Task Plan ---")
        sections.append(f"Goal: {plan.get('goal', '')}")
        for step in plan.get("steps", []):
            sections.append(
                f"  {step.get('step_number', '?')}. {step.get('description', '')}"
            )
        notes = plan.get("architecture_notes", "")
        if notes:
            sections.append(f"Architecture notes: {notes}")

    # Add review feedback if this is a re-generation after review
    review = state.get("review", {})
    if review and not review.get("approved", True):
        sections.append("\n--- Reviewer Feedback (fix these issues) ---")
        for issue in review.get("issues", []):
            sections.append(
                f"• [{issue.get('severity', '?')}] {issue.get('description', '')} "
                f"→ {issue.get('suggestion', '')}"
            )

    sections.append(f"\n--- Goal ---\n{state.get('goal', '')}")

    return "\n".join(sections)


def developer_node(
    state: AgentState,
    llm_generate: Any,
) -> AgentState:
    """Generate code implementations from the task plan.

    Args:
        state: Current workflow state with plan and context.
        llm_generate: Callable that takes a prompt and returns text.

    Returns:
        Updated state with code_outputs populated.
    """
    prompt = _build_developer_prompt(state)

    try:
        raw_response = llm_generate(prompt)
        code_outputs = json.loads(raw_response)
        if not isinstance(code_outputs, list):
            code_outputs = [code_outputs]
    except json.JSONDecodeError:
        logger.warning("Developer returned invalid JSON — wrapping raw text")
        code_outputs = [
            {
                "filename": "implementation.py",
                "language": "python",
                "code": raw_response,
                "explanation": "Generated implementation",
            }
        ]
    except Exception as e:
        logger.error("Developer agent failed: %s", e)
        return {
            **state,
            "code_outputs": [],
            "error": f"Developer failed: {e}",
        }

    return {**state, "code_outputs": code_outputs}
