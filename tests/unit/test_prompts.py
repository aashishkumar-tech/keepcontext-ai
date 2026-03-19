"""Unit tests for prompt templates."""

from keepcontext_ai.graph.schemas import (
    Entity,
    GraphResult,
    Relationship,
    RelationshipType,
)
from keepcontext_ai.llm.prompts import (
    build_context_prompt,
    build_entity_extraction_prompt,
)
from keepcontext_ai.memory.schemas import MemoryEntry, MemoryResult, MemoryType

# ---------------------------------------------------------------------------
# build_context_prompt
# ---------------------------------------------------------------------------


class TestBuildContextPrompt:
    """Tests for build_context_prompt."""

    def test_query_only(self) -> None:
        prompt = build_context_prompt(query="How does auth work?")
        assert "How does auth work?" in prompt
        assert "AI assistant" in prompt

    def test_with_memory_results(self) -> None:
        entry = MemoryEntry(
            id="1",
            content="Uses JWT tokens",
            memory_type=MemoryType.DECISION,
            created_at="2025-01-01T00:00:00+00:00",
        )
        results = [MemoryResult(entry=entry, score=0.95)]

        prompt = build_context_prompt(
            query="Auth?",
            memory_results=results,
        )
        assert "Relevant Project Knowledge" in prompt
        assert "JWT tokens" in prompt
        assert "decision" in prompt
        assert "0.95" in prompt

    def test_with_graph_result(self) -> None:
        graph = GraphResult(
            entities=[Entity(name="AuthService", entity_type="Service")],
            relationships=[
                Relationship(
                    source="AuthService",
                    target="UserModel",
                    relationship_type=RelationshipType.USES,
                )
            ],
        )

        prompt = build_context_prompt(query="test", graph_result=graph)
        assert "Architecture Relationships" in prompt
        assert "AuthService" in prompt
        assert "USES" in prompt
        assert "UserModel" in prompt

    def test_empty_graph_not_included(self) -> None:
        graph = GraphResult(entities=[], relationships=[])
        prompt = build_context_prompt(query="test", graph_result=graph)
        assert "Architecture" not in prompt

    def test_none_context(self) -> None:
        prompt = build_context_prompt(
            query="test",
            memory_results=None,
            graph_result=None,
        )
        assert "Relevant Project Knowledge" not in prompt
        assert "Architecture" not in prompt

    def test_multiple_memory_results(self) -> None:
        entries = []
        for i in range(3):
            entry = MemoryEntry(
                id=str(i),
                content=f"Memory {i}",
                memory_type=MemoryType.CODE,
                created_at="2025-01-01T00:00:00+00:00",
            )
            entries.append(MemoryResult(entry=entry, score=0.9 - i * 0.1))

        prompt = build_context_prompt(query="test", memory_results=entries)
        assert "1." in prompt
        assert "2." in prompt
        assert "3." in prompt


# ---------------------------------------------------------------------------
# build_entity_extraction_prompt
# ---------------------------------------------------------------------------


class TestBuildEntityExtractionPrompt:
    """Tests for build_entity_extraction_prompt."""

    def test_contains_text(self) -> None:
        prompt = build_entity_extraction_prompt("AuthService uses JWT")
        assert "AuthService uses JWT" in prompt

    def test_asks_for_json(self) -> None:
        prompt = build_entity_extraction_prompt("test text")
        assert "JSON" in prompt

    def test_lists_relationship_types(self) -> None:
        prompt = build_entity_extraction_prompt("test")
        assert "USES" in prompt
        assert "DEPENDS_ON" in prompt
        assert "IMPLEMENTS" in prompt

    def test_asks_for_entities_and_relationships(self) -> None:
        prompt = build_entity_extraction_prompt("test")
        assert "entities" in prompt
        assert "relationships" in prompt
