"""
Neo4j database connection management for the FastAPI application.
Provides functions to initialise and close the Neo4j driver, as well as an async context manager
for obtaining a session to run Cypher queries.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver

from config import settings

_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised. Call init_driver() first.")
    return _driver


async def init_driver() -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    await _driver.verify_connectivity()


async def close_driver() -> None:
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


@asynccontextmanager
async def get_session() -> AsyncGenerator:
    async with get_driver().session(database="neo4j") as session:
        yield session
