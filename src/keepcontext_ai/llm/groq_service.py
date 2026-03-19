"""Groq LLM service for intelligent response generation.

Provides a typed interface around Groq's API for generating
context-enriched responses to developer questions.
"""

from groq import Groq, GroqError

from keepcontext_ai.exceptions import LLMError
from keepcontext_ai.graph.schemas import GraphResult
from keepcontext_ai.llm.prompts import build_context_prompt
from keepcontext_ai.memory.schemas import MemoryResult


class GroqLLMService:
    """Generates intelligent responses using Groq LLM.

    Attributes:
        _client: The Groq client instance.
        _model: The LLM model to use.
        _max_tokens: Maximum tokens for the response.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 2048,
    ) -> None:
        """Initialize the Groq LLM service.

        Args:
            api_key: Groq API key.
            model: LLM model name.
            max_tokens: Maximum response tokens.

        Raises:
            LLMError: If the Groq client cannot be initialized.
        """
        try:
            self._client = Groq(api_key=api_key)
            self._model = model
            self._max_tokens = max_tokens
        except Exception as e:
            raise LLMError(
                message="Failed to initialize Groq client",
                code="llm_init_error",
            ) from e

    def generate(self, prompt: str) -> str:
        """Generate a response from a plain prompt.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The generated text response.

        Raises:
            LLMError: If the prompt is empty or the API call fails.
        """
        if not prompt.strip():
            raise LLMError(
                message="Cannot generate response for empty prompt",
                code="llm_empty_input",
            )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self._max_tokens,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            return content or ""
        except GroqError as e:
            raise LLMError(
                message=f"Groq API request failed: {e}",
                code="llm_api_error",
            ) from e
        except Exception as e:
            raise LLMError(
                message="Unexpected error during LLM generation",
                code="llm_unexpected_error",
            ) from e

    def generate_with_context(
        self,
        query: str,
        memory_results: list[MemoryResult] | None = None,
        graph_result: GraphResult | None = None,
    ) -> str:
        """Generate a context-enriched response.

        Combines vector search results and graph context with the
        user query into a structured prompt, then sends to Groq.

        Args:
            query: The user's natural language question.
            memory_results: Relevant vector search results.
            graph_result: Related graph entities and relationships.

        Returns:
            The generated text response.

        Raises:
            LLMError: If prompt construction or API call fails.
        """
        prompt = build_context_prompt(
            query=query,
            memory_results=memory_results,
            graph_result=graph_result,
        )
        return self.generate(prompt)
