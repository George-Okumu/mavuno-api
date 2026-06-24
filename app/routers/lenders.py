from fastapi import APIRouter, HTTPException, Query

from db.neo4j import get_session
from models.schemas import LenderOut, LenderApplicantOut

router = APIRouter(prefix="/lenders", tags=["Lenders"])


@router.get("/", response_model=list[LenderOut])
async def list_lenders():
    cypher = """
        MATCH (lb:LenderBank)
        RETURN
            lb.lenderId   AS lenderId,
            lb.lenderName AS lenderName,
            lb.lenderType AS lenderType,
            lb.country    AS country
        ORDER BY lb.lenderName
    """
    async with get_session() as session:
        result = await session.run(cypher)
        records = await result.data()
    return records


@router.get("/{lender_id}", response_model=LenderOut)
async def get_lender(lender_id: str):
    cypher = """
        MATCH (lb:LenderBank {lenderId: $lenderId})
        RETURN
            lb.lenderId   AS lenderId,
            lb.lenderName AS lenderName,
            lb.lenderType AS lenderType,
            lb.country    AS country
    """
    async with get_session() as session:
        result = await session.run(cypher, lenderId=lender_id)
        record = await result.single()
    if not record:
        raise HTTPException(status_code=404, detail=f"Lender '{lender_id}' not found")
    return dict(record)


@router.get("/{lender_id}/applicants", response_model=list[LenderApplicantOut])
async def get_lender_applicants(
    lender_id: str,
    min_score: float | None = Query(None, description="Minimum credit readiness score"),
    readiness_level: str | None = Query(None, description="Filter by readiness level"),
):
    where_extra = ""
    params: dict = {"lenderId": lender_id}

    if min_score is not None:
        where_extra += " AND cp.score >= $minScore"
        params["minScore"] = min_score
    if readiness_level:
        where_extra += " AND cp.readinessLevel = $readinessLevel"
        params["readinessLevel"] = readiness_level

    cypher = f"""
        MATCH (f:Farmer)-[al:APPLIES_TO]->(lb:LenderBank {{lenderId: $lenderId}})
        OPTIONAL MATCH (f)-[:HAS_CREDIT_PROFILE]->(cp:CreditReadinessProfile)
        WHERE true {where_extra}
        RETURN
            f.farmerId        AS farmerId,
            f.fullName        AS fullName,
            cp.score          AS creditScore,
            cp.readinessLevel AS readinessLevel,
            al.appliedAt      AS appliedAt
        ORDER BY cp.score DESC
    """
    async with get_session() as session:
        result = await session.run(cypher, params)
        records = await result.data()
    return records
