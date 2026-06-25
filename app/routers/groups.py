"""
group endpoints for listing farmer groups, getting group details, and retrieving group members.
"""

from fastapi import APIRouter, HTTPException, Query

from db.neo4j import get_session
from models.schemas import FarmerGroupOut, FarmerSummary

router = APIRouter(prefix="/groups", tags=["Farmer Groups"])


@router.get("/", response_model=list[FarmerGroupOut])
async def list_groups(
    group_type: str | None = Query(None, description="e.g. Cooperative, SACCO"),
    county: str | None = Query(None),
):
    cypher = """
        MATCH (g:FarmerGroup)
        WITH g
        WHERE ($groupType IS NULL OR g.groupType = $groupType)
          AND ($county IS NULL OR g.county = $county)
        RETURN
            g.groupId            AS groupId,
            g.groupName          AS groupName,
            g.groupType          AS groupType,
            g.registrationNumber AS registrationNumber,
            g.memberCount        AS memberCount,
            g.county             AS county
        ORDER BY g.groupName
    """
    async with get_session() as session:
        result = await session.run(cypher, groupType=group_type, county=county)
        records = await result.data()
    return records


@router.get("/{group_id}", response_model=FarmerGroupOut)
async def get_group(group_id: str):
    cypher = """
        MATCH (g:FarmerGroup {groupId: $groupId})
        RETURN
            g.groupId            AS groupId,
            g.groupName          AS groupName,
            g.groupType          AS groupType,
            g.registrationNumber AS registrationNumber,
            g.memberCount        AS memberCount,
            g.county             AS county
    """
    async with get_session() as session:
        result = await session.run(cypher, groupId=group_id)
        record = await result.single()
    if not record:
        raise HTTPException(status_code=404, detail=f"Group '{group_id}' not found")
    return dict(record)


@router.get("/{group_id}/members", response_model=list[FarmerSummary])
async def get_group_members(group_id: str):
    cypher = """
        MATCH (f:Farmer)-[:MEMBER_OF]->(g:FarmerGroup {groupId: $groupId})
        OPTIONAL MATCH (f)-[:OWNS]->(farm:Farm)-[:LOCATED_IN]->(loc:Location)
        OPTIONAL MATCH (f)-[:HAS_CREDIT_PROFILE]->(cp:CreditReadinessProfile)
        RETURN
            f.farmerId        AS farmerId,
            f.fullName        AS fullName,
            f.gender          AS gender,
            f.phone           AS phone,
            f.status          AS status,
            f.consentGiven    AS consentGiven,
            f.nationalId      AS nationalId,
            f.idType          AS idType,
            loc.county        AS county,
            cp.score          AS creditScore,
            cp.readinessLevel AS readinessLevel
        ORDER BY f.fullName
    """
    async with get_session() as session:
        result = await session.run(cypher, groupId=group_id)
        records = await result.data()
    return records
