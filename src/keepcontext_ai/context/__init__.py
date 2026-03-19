"""Context retrieval engine for KeepContext AI.

Provides semantic search over stored project memories,
with optional graph enrichment and LLM responses.

Usage:
    from keepcontext_ai.context import ContextRetriever, EnrichedContextResult

    retriever = ContextRetriever(chroma_client, embedding_service)
    results = retriever.query(MemoryQuery(query="How does auth work?"))
"""

from keepcontext_ai.context.retrieval import ContextRetriever
from keepcontext_ai.context.schemas import EnrichedContextResult

__all__ = [
    "ContextRetriever",
    "EnrichedContextResult",
]
