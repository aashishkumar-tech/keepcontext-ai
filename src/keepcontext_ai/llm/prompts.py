"""Prompt templates for context-enriched LLM queries.

Provides structured prompt construction for combining
vector search results and graph context with user queries.
"""

from keepcontext_ai.graph.schemas import GraphResult
from keepcontext_ai.memory.schemas import MemoryResult


def build_context_prompt(
    query: str,
    memory_results: list[MemoryResult] | None = None,
    graph_result: GraphResult | None = None,
) -> str:
    """Build a context-enriched prompt for the LLM.

    Combines the user query with relevant memories and graph
    context into a structured prompt.

    Args:
        query: The user's natural language question.
        memory_results: Relevant vector search results.
        graph_result: Related graph entities and relationships.

    Returns:
        A formatted prompt string for the LLM.
    """
    sections: list[str] = []

    # System instruction
    sections.append(
        "You are an AI assistant for a software development project. "
        "Use the provided context to answer the developer's question accurately. "
        "If the context doesn't contain enough information, say so honestly."
    )

    # Vector memory context
    if memory_results:
        sections.append("\n--- Relevant Project Knowledge ---")
        for i, result in enumerate(memory_results, 1):
            sections.append(
                f"{i}. [{result.entry.memory_type.value}] "
                f"(relevance: {result.score:.2f}): {result.entry.content}"
            )

    # Graph context
    if graph_result and (graph_result.entities or graph_result.relationships):
        sections.append("\n--- Architecture Relationships ---")
        for rel in graph_result.relationships:
            sections.append(
                f"• {rel.source} --[{rel.relationship_type.value}]--> {rel.target}"
            )
        if graph_result.entities:
            entity_names = [e.name for e in graph_result.entities]
            sections.append(f"Related entities: {', '.join(entity_names)}")

    # User question
    sections.append(f"\n--- Developer Question ---\n{query}")

    return "\n".join(sections)


def build_entity_extraction_prompt(text: str) -> str:
    """Build a prompt for extracting entities and relationships from text.

    Args:
        text: The text to extract entities from.

    Returns:
        A formatted prompt for entity extraction.
    """
    return (
        "Extract software entities and their relationships from the following text.\n"
        "Return a JSON object with two arrays:\n"
        '- "entities": each with "name" (string) and "entity_type" (string, e.g., '
        '"Service", "Model", "Feature", "Technology", "Pattern")\n'
        '- "relationships": each with "source" (string), "target" (string), '
        'and "relationship_type" (one of: USES, DEPENDS_ON, IMPLEMENTS, CONTAINS, '
        "PROTECTS, CALLS, EXTENDS, RELATED_TO)\n\n"
        "Only extract clear, explicit relationships. Do not invent connections.\n"
        "Return ONLY valid JSON, no markdown formatting.\n\n"
        f"Text:\n{text}"
    )
