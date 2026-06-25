"""
Analytics endpoints for graph statistics, credit score distribution, risk factors, county summaries, weather snapshots, and loan repayment rates.

"""

from fastapi import APIRouter, Query

from ..db.neo4j import get_session
from ..models.schemas import GraphStatsOut, WeatherSoilSnapshotOut

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/graph-stats", response_model=GraphStatsOut)
async def graph_stats():
    """Return node and relationship counts for the whole graph."""
    async with get_session() as session:
        node_result = await session.run(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC"
        )
        nodes = await node_result.data()

        rel_result = await session.run(
            "MATCH ()-[r]->() RETURN type(r) AS relationship, count(r) AS count ORDER BY count DESC"
        )
        rels = await rel_result.data()

    return {"nodes": nodes, "relationships": rels}


@router.get("/credit-score-distribution")
async def credit_score_distribution():
    """Bucket farmers by readiness level."""
    cypher = """
        MATCH (f:Farmer)-[:HAS_CREDIT_PROFILE]->(cp:CreditReadinessProfile)
        RETURN
            cp.readinessLevel AS readinessLevel,
            count(f)          AS farmerCount,
            avg(cp.score)     AS avgScore,
            min(cp.score)     AS minScore,
            max(cp.score)     AS maxScore
        ORDER BY avgScore DESC
    """
    async with get_session() as session:
        result = await session.run(cypher)
        records = await result.data()
    return records


@router.get("/top-risk-categories")
async def top_risk_categories():
    """Count risk factors by category and severity across all credit profiles."""
    cypher = """
        MATCH (cp:CreditReadinessProfile)-[:HAS_RISK]->(r:RiskFactor)
        RETURN
            r.category AS category,
            r.severity AS severity,
            count(r)   AS occurrences
        ORDER BY occurrences DESC
    """
    async with get_session() as session:
        result = await session.run(cypher)
        records = await result.data()
    return records


@router.get("/county-summary")
async def county_summary(county: str | None = Query(None)):
    """Aggregate farmer and credit stats grouped by county."""
    cypher = """
        MATCH (f:Farmer)-[:OWNS]->(farm:Farm)-[:LOCATED_IN]->(loc:Location)
        OPTIONAL MATCH (f)-[:HAS_CREDIT_PROFILE]->(cp:CreditReadinessProfile)
        WITH loc, f, farm, cp
        WHERE $county IS NULL OR loc.county = $county
        RETURN
            loc.county           AS county,
            count(DISTINCT f)    AS farmerCount,
            avg(cp.score)        AS avgCreditScore,
            count(DISTINCT farm) AS farmCount
        ORDER BY farmerCount DESC
    """
    async with get_session() as session:
        result = await session.run(cypher, county=county)
        records = await result.data()
    return records


@router.get("/weather-snapshots", response_model=list[WeatherSoilSnapshotOut])
async def recent_weather_snapshots(limit: int = Query(10, ge=1, le=100)):
    """Return the most recent weather and soil snapshots across all farms."""
    cypher = """
        MATCH (farm:Farm)-[:HAS_SNAPSHOT]->(ws:WeatherSoilSnapshot)
        RETURN
            ws.snapshotId   AS snapshotId,
            ws.source       AS source,
            ws.rainfall_mm  AS rainfall_mm,
            ws.tempMax_c    AS tempMax_c,
            ws.tempMin_c    AS tempMin_c,
            ws.droughtIndex AS droughtIndex,
            ws.soilPH       AS soilPH,
            ws.soilMoisture AS soilMoisture,
            ws.recordedAt   AS recordedAt
        ORDER BY ws.recordedAt DESC
        LIMIT $limit
    """
    async with get_session() as session:
        result = await session.run(cypher, limit=limit)
        records = await result.data()
    return records


@router.get("/loan-repayment-rate")
async def loan_repayment_rate():
    """Overall on-time repayment rate by lender type."""
    cypher = """
        MATCH (f:Farmer)-[:HAS_LOAN]->(loan:LoanHistory)
        RETURN
            loan.lenderType AS lenderType,
            count(loan)     AS totalLoans,
            sum(CASE WHEN loan.isOnTime THEN 1 ELSE 0 END) AS onTimeCount,
            round(
                100.0 * sum(CASE WHEN loan.isOnTime THEN 1 ELSE 0 END) / count(loan),
                2
            ) AS onTimePct
        ORDER BY onTimePct DESC
    """
    async with get_session() as session:
        result = await session.run(cypher)
        records = await result.data()
    return records
