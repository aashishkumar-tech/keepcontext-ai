"""LLM inference layer for KeepContext AI.

Provides Groq-powered intelligent response generation
with context-enriched prompts.

Usage:
    from keepcontext_ai.llm import GroqLLMService

    service = GroqLLMService(api_key="gsk-...")
    response = service.generate_with_context(
        query="How does auth work?",
        memory_results=results,
    )
"""

from keepcontext_ai.llm.groq_service import GroqLLMService
from keepcontext_ai.llm.prompts import (
    build_context_prompt,
    build_entity_extraction_prompt,
)

__all__ = [
    "GroqLLMService",
    "build_context_prompt",
    "build_entity_extraction_prompt",
]
