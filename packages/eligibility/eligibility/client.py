"""Neo4j client wrapper for eligibility engine."""
from __future__ import annotations

import os
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver
from dotenv import load_dotenv

load_dotenv()


class Neo4jClient:
    """Async Neo4j client for eligibility queries."""

    def __init__(self, uri: str | None = None, username: str | None = None, password: str | None = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Initialize the driver connection."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )

    async def close(self) -> None:
        """Close the driver connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def get_product_rules(self, product_id: str) -> list[dict[str, Any]]:
        """Fetch all eligibility rules for a product.

        Returns:
            List of rule dicts with keys: rule_id, rule_type, threshold_value, operator, error_message
        """
        if not self._driver:
            await self.connect()

        query = """
        MATCH (p:Product {id: $product_id})-[:HAS_RULE]->(r:Rule)
        RETURN r.rule_id AS rule_id,
               r.rule_type AS rule_type,
               r.threshold_value AS threshold_value,
               r.operator AS operator,
               r.error_message AS error_message
        ORDER BY r.rule_id
        """

        async with self._driver.session() as session:
            result = await session.run(query, product_id=product_id)
            records = await result.data()
            return records

    async def verify_connection(self) -> bool:
        """Test if Neo4j is reachable."""
        try:
            if not self._driver:
                await self.connect()
            async with self._driver.session() as session:
                result = await session.run("RETURN 1 AS num")
                record = await result.single()
                return record["num"] == 1
        except Exception:
            return False


# Singleton instance
_client: Neo4jClient | None = None


def get_client() -> Neo4jClient:
    """Get the global Neo4j client instance."""
    global _client
    if _client is None:
        _client = Neo4jClient()
    return _client
