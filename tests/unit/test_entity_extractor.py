"""Unit tests for EntityExtractor."""

import json
from unittest.mock import MagicMock

from keepcontext_ai.graph.entity_extractor import EntityExtractor
from keepcontext_ai.graph.schemas import (
    RelationshipType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_extractor() -> tuple[EntityExtractor, MagicMock, MagicMock]:
    """Create an EntityExtractor with mocked dependencies."""
    mock_llm = MagicMock()
    mock_graph = MagicMock()
    extractor = EntityExtractor(llm_service=mock_llm, graph_client=mock_graph)
    return extractor, mock_llm, mock_graph


# ---------------------------------------------------------------------------
# extract_and_store
# ---------------------------------------------------------------------------


class TestExtractAndStore:
    """Tests for the extract_and_store method."""

    def test_success(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.return_value = json.dumps(
            {
                "entities": [
                    {"name": "AuthService", "entity_type": "Service"},
                    {"name": "UserModel", "entity_type": "Model"},
                ],
                "relationships": [
                    {
                        "source": "AuthService",
                        "target": "UserModel",
                        "relationship_type": "USES",
                    },
                ],
            }
        )

        result = extractor.extract_and_store("AuthService uses UserModel")

        assert result == {"entities": 2, "relationships": 1}
        assert mock_graph.store_entity.call_count == 2
        assert mock_graph.store_relationship.call_count == 1

    def test_llm_failure_returns_zero(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.side_effect = RuntimeError("LLM down")

        result = extractor.extract_and_store("some text")

        assert result == {"entities": 0, "relationships": 0}
        mock_graph.store_entity.assert_not_called()

    def test_invalid_json_returns_zero(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.return_value = "not valid json {{"

        result = extractor.extract_and_store("some text")

        assert result == {"entities": 0, "relationships": 0}

    def test_empty_entities_skipped(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.return_value = json.dumps(
            {
                "entities": [
                    {"name": "", "entity_type": "Service"},
                    {"name": "Valid", "entity_type": ""},
                    {"name": "Good", "entity_type": "Model"},
                ],
                "relationships": [],
            }
        )

        result = extractor.extract_and_store("text")

        assert result["entities"] == 1  # Only "Good" stored
        assert mock_graph.store_entity.call_count == 1

    def test_invalid_relationship_type_defaults_to_related(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.return_value = json.dumps(
            {
                "entities": [],
                "relationships": [
                    {
                        "source": "A",
                        "target": "B",
                        "relationship_type": "INVALID_TYPE",
                    },
                ],
            }
        )

        result = extractor.extract_and_store("text")

        assert result["relationships"] == 1
        call_args = mock_graph.store_relationship.call_args[0][0]
        assert call_args.relationship_type == RelationshipType.RELATED_TO

    def test_graph_store_failure_continues(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.return_value = json.dumps(
            {
                "entities": [
                    {"name": "A", "entity_type": "Service"},
                    {"name": "B", "entity_type": "Model"},
                ],
                "relationships": [],
            }
        )
        # First call fails, second succeeds
        mock_graph.store_entity.side_effect = [RuntimeError("fail"), MagicMock()]

        result = extractor.extract_and_store("text")

        assert result["entities"] == 1  # Only B stored
        assert mock_graph.store_entity.call_count == 2

    def test_missing_keys_in_response(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.return_value = json.dumps({})

        result = extractor.extract_and_store("text")

        assert result == {"entities": 0, "relationships": 0}

    def test_relationship_missing_fields_skipped(self) -> None:
        extractor, mock_llm, mock_graph = _make_extractor()
        mock_llm.generate.return_value = json.dumps(
            {
                "entities": [],
                "relationships": [
                    {"source": "A", "target": "", "relationship_type": "USES"},
                    {"source": "", "target": "B", "relationship_type": "USES"},
                    {"source": "A", "target": "B", "relationship_type": ""},
                ],
            }
        )

        result = extractor.extract_and_store("text")

        assert result["relationships"] == 0
