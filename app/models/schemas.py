from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, field_validator

Role = Literal["farmer", "lender"]


#  Request bodies


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    region: Optional[str] = None
    role: Role = "farmer"

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name is required.")
        return v.strip()


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refreshToken: str


# ── Response bodies ─────────────────────────────────────────────────────────


class UserOut(BaseModel):
    userId: str
    name: str
    email: str
    role: Role
    phone: Optional[str] = None
    region: Optional[str] = None
    createdAt: Optional[datetime] = None


class AuthOut(BaseModel):
    """Returned on both login and register."""
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    user: UserOut


class MessageOut(BaseModel):
    message: str


# ── Farmer ─────────────────────────────────────────────────────────────────


class FarmerBase(BaseModel):
    farmerId: str
    fullName: str
    gender: str
    phone: str
    status: str
    consentGiven: bool
    nationalId: str
    idType: str


class FarmerDetail(FarmerBase):
    dob: Optional[date] = None
    verifiedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class FarmerSummary(FarmerBase):
    creditScore: Optional[float] = None
    readinessLevel: Optional[str] = None
    county: Optional[str] = None


# ── Farm ────────────────────────────────────────────────────────────────────


class FarmOut(BaseModel):
    farmId: str
    farmName: str
    sizeAcres: float
    ownershipType: str
    county: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    cropsGrown: list[str] = []
    createdAt: Optional[datetime] = None


# ── Credit Readiness ────────────────────────────────────────────────────────


class RiskFactorOut(BaseModel):
    riskId: str
    category: str
    severity: str
    description: str


class RecommendationOut(BaseModel):
    recommendationId: str
    title: str
    description: str
    priority: str


class AIModelRunOut(BaseModel):
    runId: str
    modelVersion: str
    explainURL: str
    runAt: Optional[datetime] = None


class CreditProfileOut(BaseModel):
    scoreId: str
    score: float
    readinessLevel: str
    confidenceLevel: float
    updatedAt: Optional[datetime] = None
    risks: list[RiskFactorOut] = []
    recommendations: list[RecommendationOut] = []
    modelRun: Optional[AIModelRunOut] = None


# ── Financial ───────────────────────────────────────────────────────────────


class FinancialProfileOut(BaseModel):
    profileId: str
    totalRevenue: float
    totalExpenses: float
    cashFlowScore: float
    computedAt: Optional[datetime] = None


class ExpenseOut(BaseModel):
    expenseId: str
    category: str
    amount: float
    currency: str
    description: str
    createdAt: Optional[datetime] = None


# ── Production & Sales ──────────────────────────────────────────────────────


class SalesTransactionOut(BaseModel):
    saleId: str
    quantity: float
    amount: float
    currency: str
    buyerType: str
    buyerName: str
    hasEvidence: bool = False
    createdAt: Optional[datetime] = None


class ProductionRecordOut(BaseModel):
    productionId: str
    productionDate: Optional[date] = None
    quantity: float
    unit: str
    season: str
    cropName: Optional[str] = None
    sales: list[SalesTransactionOut] = []


# ── Loan History ────────────────────────────────────────────────────────────


class LoanHistoryOut(BaseModel):
    loanId: str
    lenderName: str
    lenderType: str
    loanAmount: float
    repaidAmount: float
    currency: str
    isOnTime: bool
    status: str
    startDate: Optional[date] = None
    closedDate: Optional[date] = None


# ── Farmer Group ────────────────────────────────────────────────────────────


class FarmerGroupOut(BaseModel):
    groupId: str
    groupName: str
    groupType: str
    registrationNumber: str
    memberCount: int
    county: str


# ── Lender ──────────────────────────────────────────────────────────────────


class LenderOut(BaseModel):
    lenderId: str
    lenderName: str
    lenderType: str
    country: str


class LenderApplicantOut(BaseModel):
    farmerId: str
    fullName: str
    creditScore: Optional[float] = None
    readinessLevel: Optional[str] = None
    appliedAt: Optional[datetime] = None


# ── Weather / Soil ──────────────────────────────────────────────────────────


class WeatherSoilSnapshotOut(BaseModel):
    snapshotId: str
    source: str
    rainfall_mm: float
    tempMax_c: float
    tempMin_c: float
    droughtIndex: float
    soilPH: float
    soilMoisture: float
    recordedAt: Optional[datetime] = None


# ── Graph Stats ─────────────────────────────────────────────────────────────


class NodeCount(BaseModel):
    label: str
    count: int


class RelationshipCount(BaseModel):
    relationship: str
    count: int


class GraphStatsOut(BaseModel):
    nodes: list[NodeCount]
    relationships: list[RelationshipCount]
