from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel

from keepcontext_ai.graph.schemas import (
    EntityCreate,
    RelationshipCreate,
    RelationshipType,
)

if TYPE_CHECKING:
    from keepcontext_ai.graph.neo4j_client import KnowledgeGraphClient
    from keepcontext_ai.llm.groq_service import GroqLLMService

logger = logging.getLogger(__name__)

# Valid relationship type values for validation
_VALID_REL_TYPES = {rt.value for rt in RelationshipType}


# Protocol for LLM service
class LLMService(Protocol):
    def generate(self, prompt: str) -> str: ...


# --- Day 3: Pydantic models for structured extraction ---

# Valid relationship type values for validation
_VALID_REL_TYPES = {rt.value for rt in RelationshipType}


# --- Day 3: Pydantic models for structured extraction ---


class Entity(BaseModel):
    name: str
    entity_type: str  # technology | concept | decision | person | service
    description: str


class Relationship(BaseModel):
    source: str
    target: str
    relationship_type: str  # uses | implements | depends_on | replaces | configures


class ExtractionResult(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]


def build_structured_entity_extraction_prompt(text: str) -> str:
    """Prompt for extracting entities (with description) and relationships."""
    return (
        f"Analyze this technical note. Extract:\n"
        f"1. ENTITIES: technologies, concepts, components, decisions\n"
        f"2. RELATIONSHIPS: how they connect\n\n"
        f"Text: {text}\n\n"
        "Entity fields: name, entity_type (technology, concept, decision, service, person), description\n"
        "Relationship fields: source, target, relationship_type (uses, implements, depends_on, replaces, configures)\n"
        "Return a JSON object with 'entities' and 'relationships' arrays."
    )


def extract_entities_and_relationships(
    llm_service: LLMService, text: str
) -> ExtractionResult:
    """Extract entities and relationships (with descriptions) using LLM and return structured result."""
    prompt = build_structured_entity_extraction_prompt(text)
    raw_response = llm_service.generate(prompt)
    try:
        data = ExtractionResult.parse_raw(raw_response)
    except Exception:
        logger.warning("Failed to parse structured extraction result")
        raise
    return data


class EntityExtractor:
    """Extracts entities and relationships from text using LLM.

    Uses Groq LLM to parse text and identify software entities
    (services, models, features, etc.) and their relationships,
    then stores them in the knowledge graph.

    Attributes:
        _llm: Groq LLM service for text analysis.
        _graph: Neo4j client for storing extracted entities.
    """

    def __init__(
        self,
        llm_service: GroqLLMService,
        graph_client: KnowledgeGraphClient,
    ) -> None:
        """Initialize the entity extractor.

        Args:
            llm_service: Groq LLM service for entity extraction.
            graph_client: Neo4j client for storing results.
        """
        self._llm = llm_service
        self._graph = graph_client

    def extract_and_store(self, text: str) -> dict[str, int]:
        """Extract entities and relationships from text, store in graph.

        Args:
            text: The text to extract entities from (e.g., memory content).

        Returns:
            Dict with counts: {"entities": N, "relationships": M}.
        """
        from keepcontext_ai.llm.prompts import build_entity_extraction_prompt

        prompt = build_entity_extraction_prompt(text)

        try:
            raw_response = self._llm.generate(prompt)
        except Exception:
            logger.warning("LLM entity extraction failed — skipping")
            return {"entities": 0, "relationships": 0}

        return self._parse_and_store(raw_response)

    def _parse_and_store(self, raw_json: str) -> dict[str, int]:
        """Parse the LLM JSON response and store entities/relationships.

        Args:
            raw_json: Raw JSON string from the LLM.

        Returns:
            Dict with counts of stored entities and relationships.
        """
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning("Failed to parse entity extraction JSON")
            return {"entities": 0, "relationships": 0}

        entity_count = 0
        rel_count = 0

        # Store entities
        for entity_data in data.get("entities", []):
            name = entity_data.get("name", "").strip()
            entity_type = entity_data.get("entity_type", "").strip()
            if not name or not entity_type:
                continue
            try:
                self._graph.store_entity(
                    EntityCreate(name=name, entity_type=entity_type)
                )
                entity_count += 1
            except Exception:
                logger.warning("Failed to store extracted entity: %s", name)

        # Store relationships
        for rel_data in data.get("relationships", []):
            source = rel_data.get("source", "").strip()
            target = rel_data.get("target", "").strip()
            rel_type_str = rel_data.get("relationship_type", "").strip()
            if not source or not target or not rel_type_str:
                continue
            if rel_type_str not in _VALID_REL_TYPES:
                rel_type_str = "RELATED_TO"
            try:
                self._graph.store_relationship(
                    RelationshipCreate(
                        source=source,
                        target=target,
                        relationship_type=RelationshipType(rel_type_str),
                    )
                )
                rel_count += 1
            except Exception:
                logger.warning(
                    "Failed to store extracted relationship: %s -> %s",
                    source,
                    target,
                )

        return {"entities": entity_count, "relationships": rel_count}
