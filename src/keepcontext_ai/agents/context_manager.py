"""Context Manager agent node.

Retrieves relevant project knowledge from vector memory and
knowledge graph, enriching the workflow state before other
agents process the request.
"""

from __future__ import annotations

import logging

from keepcontext_ai.agents.schemas import AgentState
from keepcontext_ai.context.retrieval import ContextRetriever
from keepcontext_ai.memory.schemas import MemoryQuery

logger = logging.getLogger(__name__)


def context_manager_node(
    state: AgentState,
    retriever: ContextRetriever,
) -> AgentState:
    """Retrieve relevant context and enrich the workflow state.

    Queries ChromaDB for semantically similar memories and
    optionally traverses Neo4j for graph relationships.

    Args:
        state: Current workflow state with the developer goal.
        retriever: The context retriever (vector + graph + LLM).

    Returns:
        Updated state with context_results and graph_context populated.
    """
    goal = state.get("goal", "")
    entity_name = None

    # Try to extract an entity name from the goal for graph lookup.
    # Heuristic: pick the first CamelCase / PascalCase identifier, or
    # falling back to the first capitalised word that is NOT a common
    # English sentence-starter.
    common_words = frozenset(
        {
            "A",
            "An",
            "The",
            "This",
            "That",
            "These",
            "Those",
            "How",
            "What",
            "When",
            "Where",
            "Why",
            "Which",
            "Who",
            "Can",
            "Could",
            "Would",
            "Should",
            "Does",
            "Did",
            "Do",
            "Is",
            "Are",
            "Was",
            "Were",
            "Will",
            "Has",
            "Have",
            "Had",
            "Show",
            "Tell",
            "Give",
            "Find",
            "Get",
            "Set",
            "Let",
            "Explain",
            "Describe",
            "List",
            "Create",
            "Build",
            "Add",
            "Remove",
            "Delete",
            "Update",
            "Fix",
            "Make",
            "Run",
            "Please",
            "Help",
            "Use",
            "Using",
            "Define",
            "Implement",
            "Write",
            "Read",
            "Check",
            "Test",
            "I",
            "We",
            "You",
            "My",
            "Our",
            "Your",
            "It",
            "Its",
            "For",
            "From",
            "With",
            "About",
            "Into",
            "Also",
            "And",
            "But",
            "Or",
            "Not",
            "All",
            "Any",
            "Each",
            "Every",
            "Some",
            "No",
            "If",
            "Then",
            "So",
            "Just",
            "Only",
            "Now",
            "Here",
        }
    )
    words = goal.split()
    for word in words:
        stripped = word.strip("\"'`.,!?;:()")
        if not stripped or len(stripped) <= 2:
            continue
        # Prefer identifiers with mixed case (e.g. UserService, getData)
        has_upper = any(c.isupper() for c in stripped)
        has_lower = any(c.islower() for c in stripped)
        if has_upper and has_lower and stripped not in common_words:
            entity_name = stripped
            break
        # Accept ALL-CAPS identifiers (e.g. API, JWT) — but skip commons
        if stripped[0].isupper() and stripped not in common_words:
            entity_name = stripped
            break

    try:
        query = MemoryQuery(query=goal, top_k=5)
        enriched = retriever.query_enriched(
            request=query,
            entity_name=entity_name,
            use_llm=False,  # Don't use LLM here — agents will use it later
        )

        context_results = [
            {
                "content": r.entry.content,
                "memory_type": r.entry.memory_type.value,
                "score": r.score,
            }
            for r in enriched.memory_results
        ]

        graph_context = enriched.graph_context.model_dump()

        logger.info(
            "Context manager retrieved %d memories, %d graph entities",
            len(context_results),
            len(enriched.graph_context.entities),
        )

    except Exception:
        logger.warning("Context retrieval failed — proceeding without context")
        context_results = []
        graph_context = {"entities": [], "relationships": []}

    return {
        **state,
        "context_results": context_results,
        "graph_context": graph_context,
    }
