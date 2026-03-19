"""OpenAI embedding service for converting text to vectors.

Provides a typed interface around OpenAI's embedding API.
Used to generate embeddings before storing in ChromaDB
and when querying for semantic search.
"""

from openai import OpenAI, OpenAIError

from keepcontext_ai.exceptions import EmbeddingError


class EmbeddingService:
    """Generates vector embeddings from text using OpenAI's API.

    Attributes:
        _client: The OpenAI client instance.
        _model: The embedding model to use.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
    ) -> None:
        """Initialize the embedding service.

        Args:
            api_key: OpenAI API key.
            model: Embedding model name.

        Raises:
            EmbeddingError: If the OpenAI client cannot be initialized.
        """
        try:
            self._client = OpenAI(api_key=api_key)
            self._model = model
        except Exception as e:
            raise EmbeddingError(
                message="Failed to initialize OpenAI client",
                code="embedding_init_error",
            ) from e

    def generate(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: The input text to embed. Must not be empty.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            EmbeddingError: If the text is empty or API call fails.
        """
        if not text.strip():
            raise EmbeddingError(
                message="Cannot generate embedding for empty text",
                code="embedding_empty_input",
            )

        try:
            response = self._client.embeddings.create(
                input=text,
                model=self._model,
            )
            return response.data[0].embedding
        except OpenAIError as e:
            raise EmbeddingError(
                message=f"OpenAI embedding request failed: {e}",
                code="embedding_api_error",
            ) from e
        except Exception as e:
            raise EmbeddingError(
                message="Unexpected error during embedding generation",
                code="embedding_unexpected_error",
            ) from e

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a single API call.

        More efficient than calling generate() in a loop, as it batches
        the texts into a single API request.

        Args:
            texts: List of input texts to embed. Must not be empty.

        Returns:
            A list of embedding vectors, one per input text.

        Raises:
            EmbeddingError: If any text is empty, the list is empty,
                or the API call fails.
        """
        if not texts:
            raise EmbeddingError(
                message="Cannot generate embeddings for empty text list",
                code="embedding_empty_batch",
            )

        stripped_texts = [t.strip() for t in texts]
        if any(not t for t in stripped_texts):
            raise EmbeddingError(
                message="Cannot generate embedding for empty text in batch",
                code="embedding_empty_input",
            )

        try:
            response = self._client.embeddings.create(
                input=stripped_texts,
                model=self._model,
            )
            # Sort by index to ensure order matches input
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except OpenAIError as e:
            raise EmbeddingError(
                message=f"OpenAI batch embedding request failed: {e}",
                code="embedding_api_error",
            ) from e
        except Exception as e:
            raise EmbeddingError(
                message="Unexpected error during batch embedding generation",
                code="embedding_unexpected_error",
            ) from e
