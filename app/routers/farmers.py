"""
Farmers endpoints for listing farmers, getting farmer details, and retrieving related data such as farms, credit profiles, financial profiles, expenses, production records, and loan history.
"""

from fastapi import APIRouter, HTTPException, Query

from ..db.neo4j import get_session
from ..models.schemas import (
    CreditProfileOut,
    ExpenseOut,
    FarmerDetail,
    FarmerSummary,
    FarmOut,
    FinancialProfileOut,
    LoanHistoryOut,
    ProductionRecordOut,
)

router = APIRouter(prefix="/farmers", tags=["Farmers"])


# List farmers

@router.get("/", response_model=list[FarmerSummary])
async def list_farmers(
    status: str | None = Query(None, description="Filter by farmer status"),
    county: str | None = Query(None, description="Filter by county"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """Return a paginated list of farmers with their latest credit score and location."""
    cypher = """
        MATCH (f:Farmer)
        OPTIONAL MATCH (f)-[:OWNS]->(farm:Farm)-[:LOCATED_IN]->(loc:Location)
        OPTIONAL MATCH (f)-[:HAS_CREDIT_PROFILE]->(cp:CreditReadinessProfile)
        WITH f, loc, cp
        WHERE ($status IS NULL OR f.status = $status)
          AND ($county IS NULL OR loc.county = $county)
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
        SKIP $skip LIMIT $limit
    """
    async with get_session() as session:
        result = await session.run(
            cypher,
            status=status,
            county=county,
            skip=skip,
            limit=limit,
        )
        records = await result.data()
    return records


# Get farmer detail

@router.get("/{farmer_id}", response_model=FarmerDetail)
async def get_farmer(farmer_id: str):
    cypher = """
        MATCH (f:Farmer {farmerId: $farmerId})
        RETURN
            f.farmerId     AS farmerId,
            f.fullName     AS fullName,
            f.gender       AS gender,
            f.phone        AS phone,
            f.status       AS status,
            f.consentGiven AS consentGiven,
            f.nationalId   AS nationalId,
            f.idType       AS idType,
            f.dob          AS dob,
            f.verifiedAt   AS verifiedAt,
            f.createdAt    AS createdAt,
            f.updatedAt    AS updatedAt
    """
    async with get_session() as session:
        result = await session.run(cypher, farmerId=farmer_id)
        record = await result.single()
    if not record:
        raise HTTPException(status_code=404, detail=f"Farmer '{farmer_id}' not found")
    return dict(record)


# Farmer farms

@router.get("/{farmer_id}/farms", response_model=list[FarmOut])
async def get_farmer_farms(farmer_id: str):
    async with get_session() as session:
        check = await session.run(
            "MATCH (f:Farmer {farmerId: $farmerId}) RETURN f LIMIT 1",
            farmerId=farmer_id,
        )
        if await check.single() is None:
            raise HTTPException(status_code=404, detail=f"Farmer '{farmer_id}' not found")

        result = await session.run(
            """
            MATCH (f:Farmer {farmerId: $farmerId})-[:OWNS]->(farm:Farm)
            OPTIONAL MATCH (farm)-[:LOCATED_IN]->(loc:Location)
            OPTIONAL MATCH (farm)-[:GROWS]->(c:Crop)
            RETURN
                farm.farmId        AS farmId,
                farm.farmName      AS farmName,
                farm.sizeAcres     AS sizeAcres,
                farm.ownershipType AS ownershipType,
                farm.createdAt     AS createdAt,
                loc.county         AS county,
                loc.village        AS village,
                loc.latitude       AS latitude,
                loc.longitude      AS longitude,
                collect(c.cropName) AS cropsGrown
            """,
            farmerId=farmer_id,
        )
        records = await result.data()
    return records



@router.get("/{farmer_id}/credit-profile", response_model=CreditProfileOut)
async def get_credit_profile(farmer_id: str):
    cypher = """
        MATCH (f:Farmer {farmerId: $farmerId})-[:HAS_CREDIT_PROFILE]->(cp:CreditReadinessProfile)
        OPTIONAL MATCH (cp)-[:HAS_RISK]->(r:RiskFactor)
        OPTIONAL MATCH (cp)-[:RECOMMENDED]->(rec:Recommendation)
        OPTIONAL MATCH (cp)-[:GENERATED_BY]->(ai:AIModelRun)
        RETURN
            cp.scoreId         AS scoreId,
            cp.score           AS score,
            cp.readinessLevel  AS readinessLevel,
            cp.confidenceLevel AS confidenceLevel,
            cp.updatedAt       AS updatedAt,
            collect(DISTINCT {
                riskId:      r.riskId,
                category:    r.category,
                severity:    r.severity,
                description: r.description
            }) AS risks,
            collect(DISTINCT {
                recommendationId: rec.recommendationId,
                title:            rec.title,
                description:      rec.description,
                priority:         rec.priority
            }) AS recommendations,
            CASE WHEN ai IS NOT NULL THEN {
                runId:        ai.runId,
                modelVersion: ai.modelVersion,
                explainURL:   ai.explainURL,
                runAt:        ai.runAt
            } ELSE null END AS modelRun
    """
    async with get_session() as session:
        result = await session.run(cypher, farmerId=farmer_id)
        record = await result.single()
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"No credit profile for farmer '{farmer_id}'",
        )
    data = dict(record)
    data["risks"] = [r for r in data["risks"] if r.get("riskId")]
    data["recommendations"] = [r for r in data["recommendations"] if r.get("recommendationId")]
    return data


# ── Financial profile ─────────────────────────────────────────────────────────

@router.get("/{farmer_id}/financial-profile", response_model=FinancialProfileOut)
async def get_financial_profile(farmer_id: str):
    cypher = """
        MATCH (f:Farmer {farmerId: $farmerId})-[:HAS_FINANCIAL_PROFILE]->(fp:FinancialProfile)
        RETURN
            fp.profileId     AS profileId,
            fp.totalRevenue  AS totalRevenue,
            fp.totalExpenses AS totalExpenses,
            fp.cashFlowScore AS cashFlowScore,
            fp.computedAt    AS computedAt
    """
    async with get_session() as session:
        result = await session.run(cypher, farmerId=farmer_id)
        record = await result.single()
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"No financial profile for farmer '{farmer_id}'",
        )
    return dict(record)


# ── Expenses ──────────────────────────────────────────────────────────────────

@router.get("/{farmer_id}/expenses", response_model=list[ExpenseOut])
async def get_farmer_expenses(
    farmer_id: str,
    category: str | None = Query(None),
):
    cypher = """
        MATCH (f:Farmer {farmerId: $farmerId})-[:INCURRED]->(e:ExpenseTransaction)
        WHERE $category IS NULL OR e.category = $category
        RETURN
            e.expenseId   AS expenseId,
            e.category    AS category,
            e.amount      AS amount,
            e.currency    AS currency,
            e.description AS description,
            e.createdAt   AS createdAt
        ORDER BY e.createdAt DESC
    """
    async with get_session() as session:
        result = await session.run(cypher, farmerId=farmer_id, category=category)
        records = await result.data()
    return records


# ── Production records ────────────────────────────────────────────────────────

@router.get("/{farmer_id}/production", response_model=list[ProductionRecordOut])
async def get_production_records(farmer_id: str):
    cypher = """
        MATCH (f:Farmer {farmerId: $farmerId})-[:OWNS]->(farm:Farm)-[:GENERATES]->(pr:ProductionRecord)
        OPTIONAL MATCH (pr)-[:FOR_CROP]->(c:Crop)
        OPTIONAL MATCH (pr)-[:SOLD_AS]->(s:SalesTransaction)
        OPTIONAL MATCH (s)-[:SUPPORTED_BY]->(ev:EvidenceDocument)
        RETURN
            pr.productionId   AS productionId,
            pr.productionDate AS productionDate,
            pr.quantity       AS quantity,
            pr.unit           AS unit,
            pr.season         AS season,
            c.cropName        AS cropName,
            collect(DISTINCT {
                saleId:      s.saleId,
                quantity:    s.quantity,
                amount:      s.amount,
                currency:    s.currency,
                buyerType:   s.buyerType,
                buyerName:   s.buyerName,
                hasEvidence: ev IS NOT NULL,
                createdAt:   s.createdAt
            }) AS sales
        ORDER BY pr.productionDate DESC
    """
    async with get_session() as session:
        result = await session.run(cypher, farmerId=farmer_id)
        records = await result.data()
    for rec in records:
        rec["sales"] = [s for s in rec["sales"] if s.get("saleId")]
    return records


# ── Loan history ──────────────────────────────────────────────────────────────

@router.get("/{farmer_id}/loans", response_model=list[LoanHistoryOut])
async def get_loan_history(farmer_id: str):
    cypher = """
        MATCH (f:Farmer {farmerId: $farmerId})-[:HAS_LOAN]->(loan:LoanHistory)
        RETURN
            loan.loanId       AS loanId,
            loan.lenderName   AS lenderName,
            loan.lenderType   AS lenderType,
            loan.loanAmount   AS loanAmount,
            loan.repaidAmount AS repaidAmount,
            loan.currency     AS currency,
            loan.isOnTime     AS isOnTime,
            loan.status       AS status,
            loan.startDate    AS startDate,
            loan.closedDate   AS closedDate
        ORDER BY loan.startDate DESC
    """
    async with get_session() as session:
        result = await session.run(cypher, farmerId=farmer_id)
        records = await result.data()
    return records
