"""ChromaDB client wrapper for vector memory storage.

Provides a typed interface around ChromaDB operations.
All storage and retrieval goes through this client, isolating
ChromaDB-specific logic from the rest of the application.
"""

import uuid
from collections.abc import Mapping
from typing import Any, cast

import chromadb
from chromadb.api.models.Collection import Collection

from keepcontext_ai.exceptions import MemoryError
from keepcontext_ai.memory.schemas import (
    MemoryCreate,
    MemoryEntry,
    MemoryResult,
    MemoryType,
    create_timestamp,
)


class ChromaMemoryClient:
    """Typed wrapper around ChromaDB for memory operations.

    Handles connection management, collection setup, and provides
    CRUD + semantic search operations for memory entries.

    Attributes:
        _client: The underlying ChromaDB HTTP client.
        _collection: The ChromaDB collection for memory entries.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8100,
        collection_name: str = "keepcontext_memory",
    ) -> None:
        """Initialize the ChromaDB client and ensure collection exists.

        Args:
            host: ChromaDB server host.
            port: ChromaDB server port.
            collection_name: Name of the collection to use.

        Raises:
            MemoryError: If connection to ChromaDB fails.
        """
        try:
            self._client = chromadb.HttpClient(host=host, port=port)
            self._collection: Collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "KeepContext AI memory store"},
            )
        except Exception as e:
            raise MemoryError(
                message=f"Failed to connect to ChromaDB at {host}:{port}",
                code="memory_connection_error",
            ) from e

    def store(
        self,
        entry: MemoryCreate,
        embedding: list[float],
    ) -> MemoryEntry:
        """Store a memory entry with its embedding.

        Args:
            entry: The memory entry to store.
            embedding: Pre-computed embedding vector for the content.

        Returns:
            The stored MemoryEntry with generated ID and timestamp.

        Raises:
            MemoryError: If the storage operation fails.
        """
        memory_id = str(uuid.uuid4())
        timestamp = create_timestamp()

        metadata: dict[str, str] = {
            "memory_type": entry.memory_type.value,
            "created_at": timestamp,
            **entry.metadata,
        }

        try:
            self._collection.add(
                ids=[memory_id],
                embeddings=cast(Any, [embedding]),
                documents=[entry.content],
                metadatas=[metadata],
            )
        except Exception as e:
            raise MemoryError(
                message=f"Failed to store memory entry: {entry.content[:50]}...",
                code="memory_store_error",
            ) from e

        return MemoryEntry(
            id=memory_id,
            content=entry.content,
            memory_type=entry.memory_type,
            metadata=entry.metadata,
            created_at=timestamp,
        )

    def get(self, memory_id: str) -> MemoryEntry:
        """Retrieve a memory entry by its ID.

        Args:
            memory_id: The unique identifier of the memory entry.

        Returns:
            The matching MemoryEntry.

        Raises:
            MemoryError: If the entry is not found or retrieval fails.
        """
        try:
            result = cast(
                Mapping[str, Any],
                self._collection.get(
                    ids=[memory_id], include=["documents", "metadatas"]
                ),
            )
        except Exception as e:
            raise MemoryError(
                message=f"Failed to retrieve memory entry: {memory_id}",
                code="memory_get_error",
            ) from e

        if not result["ids"]:
            raise MemoryError(
                message=f"Memory entry not found: {memory_id}",
                code="memory_not_found",
            )

        return self._build_entry_from_result(result, index=0)

    def list_entries(
        self,
        limit: int = 20,
        offset: int = 0,
        memory_type: MemoryType | None = None,
    ) -> list[MemoryEntry]:
        """List memory entries with optional filtering.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.
            memory_type: Optional filter by memory type.

        Returns:
            List of matching MemoryEntry objects.

        Raises:
            MemoryError: If the list operation fails.
        """
        try:
            where_filter: dict[str, str] | None = None
            if memory_type is not None:
                where_filter = {"memory_type": memory_type.value}

            result = cast(
                Mapping[str, Any],
                self._collection.get(
                    include=["documents", "metadatas"],
                    limit=limit,
                    offset=offset,
                    where=cast(Any, where_filter),
                ),
            )
        except Exception as e:
            raise MemoryError(
                message="Failed to list memory entries",
                code="memory_list_error",
            ) from e

        entries: list[MemoryEntry] = []
        for i in range(len(result["ids"])):
            entries.append(self._build_entry_from_result(result, index=i))

        return entries

    def delete(self, memory_id: str) -> None:
        """Delete a memory entry by its ID.

        Args:
            memory_id: The unique identifier of the entry to delete.

        Raises:
            MemoryError: If deletion fails or entry not found.
        """
        # Verify the entry exists first
        self.get(memory_id)

        try:
            self._collection.delete(ids=[memory_id])
        except Exception as e:
            raise MemoryError(
                message=f"Failed to delete memory entry: {memory_id}",
                code="memory_delete_error",
            ) from e

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
        memory_type: MemoryType | None = None,
    ) -> list[MemoryResult]:
        """Search memory entries by embedding similarity.

        Args:
            embedding: The query embedding vector.
            top_k: Maximum number of results to return.
            memory_type: Optional filter by memory type.

        Returns:
            List of MemoryResult objects sorted by relevance.

        Raises:
            MemoryError: If the query operation fails.
        """
        try:
            where_filter: dict[str, str] | None = None
            if memory_type is not None:
                where_filter = {"memory_type": memory_type.value}

            results = self._collection.query(
                query_embeddings=cast(Any, [embedding]),
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
                where=cast(Any, where_filter),
            )
        except Exception as e:
            raise MemoryError(
                message="Failed to query memory",
                code="memory_query_error",
            ) from e

        memory_results: list[MemoryResult] = []

        if not results["ids"] or not results["ids"][0]:
            return memory_results

        ids = results["ids"][0]
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for i, memory_id in enumerate(ids):
            metadata_raw = metadatas[i] if i < len(metadatas) else {}
            metadata = (
                {k: str(v) for k, v in metadata_raw.items()} if metadata_raw else {}
            )

            memory_type_value = metadata.pop(
                "memory_type", MemoryType.DOCUMENTATION.value
            )
            created_at = metadata.pop("created_at", create_timestamp())

            entry = MemoryEntry(
                id=memory_id,
                content=documents[i] if i < len(documents) else "",
                memory_type=MemoryType(memory_type_value),
                metadata=metadata,
                created_at=created_at,
            )

            # ChromaDB returns distances; convert to similarity score (0-1)
            distance = distances[i] if i < len(distances) else 1.0
            score = max(0.0, min(1.0, 1.0 - distance))

            memory_results.append(MemoryResult(entry=entry, score=score))

        return memory_results

    def count(self) -> int:
        """Return the total number of entries in the collection.

        Returns:
            The count of stored memory entries.

        Raises:
            MemoryError: If the count operation fails.
        """
        try:
            return self._collection.count()
        except Exception as e:
            raise MemoryError(
                message="Failed to count memory entries",
                code="memory_count_error",
            ) from e

    @staticmethod
    def _build_entry_from_result(
        result: Mapping[str, Any],
        index: int,
    ) -> MemoryEntry:
        """Build a MemoryEntry from a ChromaDB result dict.

        Args:
            result: Raw ChromaDB get/query result.
            index: Index within the result arrays.

        Returns:
            A constructed MemoryEntry.
        """
        metadata_raw = result["metadatas"][index] if result.get("metadatas") else {}
        metadata = {k: str(v) for k, v in metadata_raw.items()} if metadata_raw else {}

        memory_type_value = metadata.pop("memory_type", MemoryType.DOCUMENTATION.value)
        created_at = metadata.pop("created_at", create_timestamp())

        documents = result.get("documents") or []
        content = documents[index] if index < len(documents) else ""

        return MemoryEntry(
            id=result["ids"][index],
            content=content,
            memory_type=MemoryType(memory_type_value),
            metadata=metadata,
            created_at=created_at,
        )
