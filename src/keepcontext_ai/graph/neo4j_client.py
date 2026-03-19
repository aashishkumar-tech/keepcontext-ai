"""Neo4j client wrapper for knowledge graph operations.

Provides a typed interface around Neo4j for storing and querying
entities and relationships in KeepContext AI's knowledge graph.
"""

from neo4j import Driver, GraphDatabase

from keepcontext_ai.exceptions import GraphError
from keepcontext_ai.graph.schemas import (
    Entity,
    EntityCreate,
    GraphQuery,
    GraphResult,
    Relationship,
    RelationshipCreate,
    RelationshipType,
)


class KnowledgeGraphClient:
    """Typed wrapper around Neo4j for knowledge graph operations.

    Handles connection management and provides CRUD + query
    operations for entities and relationships.

    Attributes:
        _driver: The Neo4j driver instance.
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
    ) -> None:
        """Initialize the Neo4j client.

        Args:
            uri: Neo4j connection URI.
            user: Neo4j username.
            password: Neo4j password.

        Raises:
            GraphError: If connection to Neo4j fails.
        """
        try:
            self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
            self._driver.verify_connectivity()
        except Exception as e:
            raise GraphError(
                message=f"Failed to connect to Neo4j at {uri}",
                code="graph_connection_error",
            ) from e

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self._driver.close()

    def store_entity(self, entity: EntityCreate) -> Entity:
        """Store or update an entity node in the knowledge graph.

        Uses MERGE to avoid duplicates — if an entity with the same
        name and type already exists, its properties are updated.

        Args:
            entity: The entity to store.

        Returns:
            The stored Entity.

        Raises:
            GraphError: If the storage operation fails.
        """
        query = """
        MERGE (e:Entity {name: $name, entity_type: $entity_type})
        SET e += $properties
        RETURN e.name AS name, e.entity_type AS entity_type
        """
        try:
            with self._driver.session() as session:
                result = session.run(
                    query,
                    name=entity.name,
                    entity_type=entity.entity_type,
                    properties=entity.properties,
                )
                record = result.single()
                if record is None:
                    raise GraphError(
                        message=f"Failed to store entity: {entity.name}",
                        code="graph_store_error",
                    )
                return Entity(
                    name=record["name"],
                    entity_type=record["entity_type"],
                    properties=entity.properties,
                )
        except GraphError:
            raise
        except Exception as e:
            raise GraphError(
                message=f"Failed to store entity: {entity.name}",
                code="graph_store_error",
            ) from e

    def store_relationship(self, relationship: RelationshipCreate) -> Relationship:
        """Store a relationship between two entities.

        Auto-creates source/target entities if they don't exist.

        Args:
            relationship: The relationship to store.

        Returns:
            The stored Relationship.

        Raises:
            GraphError: If the storage operation fails.
        """
        rel_type = relationship.relationship_type.value
        query = f"""
        MERGE (source:Entity {{name: $source}})
        MERGE (target:Entity {{name: $target}})
        MERGE (source)-[r:{rel_type}]->(target)
        SET r += $properties
        RETURN source.name AS source, target.name AS target
        """
        try:
            with self._driver.session() as session:
                result = session.run(
                    query,
                    source=relationship.source,
                    target=relationship.target,
                    properties=relationship.properties,
                )
                record = result.single()
                if record is None:
                    raise GraphError(
                        message=f"Failed to store relationship: {relationship.source} -> {relationship.target}",
                        code="graph_store_error",
                    )
                return Relationship(
                    source=record["source"],
                    target=record["target"],
                    relationship_type=relationship.relationship_type,
                    properties=relationship.properties,
                )
        except GraphError:
            raise
        except Exception as e:
            raise GraphError(
                message=f"Failed to store relationship: {relationship.source} -> {relationship.target}",
                code="graph_store_error",
            ) from e

    def get_entity(self, name: str) -> Entity:
        """Retrieve an entity by name.

        Args:
            name: The entity name.

        Returns:
            The matching Entity.

        Raises:
            GraphError: If the entity is not found or query fails.
        """
        query = """
        MATCH (e:Entity {name: $name})
        RETURN e.name AS name, e.entity_type AS entity_type,
               properties(e) AS props
        """
        try:
            with self._driver.session() as session:
                result = session.run(query, name=name)
                record = result.single()
                if record is None:
                    raise GraphError(
                        message=f"Entity not found: {name}",
                        code="graph_not_found",
                    )
                props = dict(record["props"])
                props.pop("name", None)
                props.pop("entity_type", None)
                return Entity(
                    name=record["name"],
                    entity_type=record["entity_type"] or "Unknown",
                    properties={k: str(v) for k, v in props.items()},
                )
        except GraphError:
            raise
        except Exception as e:
            raise GraphError(
                message=f"Failed to retrieve entity: {name}",
                code="graph_get_error",
            ) from e

    def query_relationships(self, query: GraphQuery) -> GraphResult:
        """Query the knowledge graph for related entities and relationships.

        Args:
            query: The graph query parameters.

        Returns:
            GraphResult containing discovered entities and relationships.

        Raises:
            GraphError: If the query operation fails.
        """
        rel_filter = (
            f":{query.relationship_type.value}" if query.relationship_type else ""
        )

        if query.direction == "outgoing":
            pattern = f"(source:Entity {{name: $name}})-[r{rel_filter}*1..{query.depth}]->(target:Entity)"
        elif query.direction == "incoming":
            pattern = f"(source:Entity {{name: $name}})<-[r{rel_filter}*1..{query.depth}]-(target:Entity)"
        else:
            pattern = f"(source:Entity {{name: $name}})-[r{rel_filter}*1..{query.depth}]-(target:Entity)"

        cypher = f"""
        MATCH {pattern}
        UNWIND r AS rel
        RETURN DISTINCT
            source.name AS source_name,
            target.name AS target_name,
            target.entity_type AS target_type,
            type(rel) AS rel_type
        """
        try:
            with self._driver.session() as session:
                result = session.run(cypher, name=query.entity_name)
                entities: dict[str, Entity] = {}
                relationships: list[Relationship] = []

                for record in result:
                    target_name = record["target_name"]
                    if target_name not in entities:
                        entities[target_name] = Entity(
                            name=target_name,
                            entity_type=record["target_type"] or "Unknown",
                        )

                    rel_type_str = record["rel_type"]
                    try:
                        rel_type = RelationshipType(rel_type_str)
                    except ValueError:
                        rel_type = RelationshipType.RELATED_TO

                    relationships.append(
                        Relationship(
                            source=record["source_name"],
                            target=target_name,
                            relationship_type=rel_type,
                        )
                    )

                return GraphResult(
                    entities=list(entities.values()),
                    relationships=relationships,
                )
        except GraphError:
            raise
        except Exception as e:
            raise GraphError(
                message=f"Failed to query graph for: {query.entity_name}",
                code="graph_query_error",
            ) from e

    def get_dependencies(self, entity_name: str) -> GraphResult:
        """Get all dependencies for an entity (outgoing DEPENDS_ON).

        Args:
            entity_name: Name of the entity to check.

        Returns:
            GraphResult with dependent entities and relationships.
        """
        query = GraphQuery(
            entity_name=entity_name,
            relationship_type=RelationshipType.DEPENDS_ON,
            direction="outgoing",
            depth=3,
        )
        return self.query_relationships(query)

    def impact_analysis(self, entity_name: str) -> GraphResult:
        """Determine what would be affected if an entity changes.

        Finds all entities that depend on the given entity (incoming DEPENDS_ON)
        plus anything that USES it.

        Args:
            entity_name: Name of the entity being changed.

        Returns:
            GraphResult with affected entities and relationships.
        """
        query = GraphQuery(
            entity_name=entity_name,
            direction="incoming",
            depth=3,
        )
        return self.query_relationships(query)

    def count_entities(self) -> int:
        """Return the total number of entity nodes.

        Returns:
            Count of entity nodes.

        Raises:
            GraphError: If the count operation fails.
        """
        try:
            with self._driver.session() as session:
                result = session.run("MATCH (e:Entity) RETURN count(e) AS cnt")
                record = result.single()
                return record["cnt"] if record else 0
        except Exception as e:
            raise GraphError(
                message="Failed to count entities",
                code="graph_count_error",
            ) from e

    def clear(self) -> None:
        """Delete all nodes and relationships. Use with caution.

        Raises:
            GraphError: If the clear operation fails.
        """
        try:
            with self._driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
        except Exception as e:
            raise GraphError(
                message="Failed to clear graph",
                code="graph_clear_error",
            ) from e
