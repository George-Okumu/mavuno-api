import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.neo4j import init_driver, close_driver
from routers import farmers, lenders, groups, analytics

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("mavuno")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to Neo4j Aura at %s …", settings.neo4j_uri)
    await init_driver()
    logger.info("Neo4j connection established.")
    yield
    await close_driver()
    logger.info("Neo4j connection closed.")


app = FastAPI(
    title="Mavuno API",
    description=(
        "Credit-readiness and farm risk profiling API for smallholder farmers. "
        "Backed by a Neo4j Aura graph database."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(farmers.router)
app.include_router(lenders.router)
app.include_router(groups.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Mavuno API",
        "version": "1.0.0",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    from app.db.neo4j import get_session
    async with get_session() as session:
        result = await session.run("RETURN 1 AS ping")
        record = await result.single()
    return {"status": "ok", "neo4j": "reachable", "ping": record["ping"]}
