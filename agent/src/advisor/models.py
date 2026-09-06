"""Pydantic models shared by the advisor store, service, routes and prompt."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

AccountType = Literal[
    "taxable", "roth_ira", "traditional_ira", "401k", "hsa", "crypto", "other"
]
Action = Literal["buy", "sell", "trim", "hold"]
Decision = Literal["open", "accepted", "rejected", "expired"]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ── Inputs pushed by the finance app ─────────────────────────────────────────

class PositionIn(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32)
    quantity: float = Field(..., gt=0)
    cost_basis_usd: float | None = Field(None, ge=0, description="Total cost basis")
    asset_class: Literal["stock", "etf", "crypto", "bond", "cash", "other"] | None = None

    @field_validator("symbol")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class AccountIn(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    type: AccountType = "taxable"
    cash_usd: float = Field(0.0, ge=0)
    positions: list[PositionIn] = Field(default_factory=list)


class HoldingsIn(BaseModel):
    accounts: list[AccountIn] = Field(..., min_length=1)
    source: str = Field("finance-app", max_length=64)
    as_of: str | None = Field(None, description="ISO date the app fetched balances")


class Objectives(BaseModel):
    """The client mandate the wealth manager reviews against."""

    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "aggressive"
    horizon_years: int = Field(10, ge=1, le=60)
    single_stock_sleeve_cap: float = Field(0.40, ge=0, le=1, description="Max share of total in individual stocks")
    max_position_weight: float = Field(0.15, ge=0, le=1)
    benchmark: str = "SPY"
    notes: str = Field("", max_length=2000)


class ReviewRequest(BaseModel):
    snapshot_id: str | None = None
    objectives: Objectives = Field(default_factory=Objectives)


class DecisionIn(BaseModel):
    status: Literal["accepted", "rejected"]
    note: str = Field("", max_length=1000)


# ── LLM output contract (what the model must return) ─────────────────────────

class RecommendationOut(BaseModel):
    action: Action
    symbol: str = Field(..., min_length=1, max_length=32)
    account_id: str | None = Field(None, description="Which account to act in; null = advisor's choice")
    amount_usd: float | None = Field(None, gt=0, description="Dollars to buy or sell; omit for hold or full sell")
    target_weight: float | None = Field(None, ge=0, le=1, description="Desired weight of total portfolio after the trade")
    rationale: str = Field(..., min_length=10, max_length=1200)
    confidence: float = Field(..., ge=0, le=1)
    horizon: Literal["weeks", "months", "years"] = "years"
    tax_note: str = Field("", max_length=600)
    is_new_position: bool = False

    @field_validator("symbol")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class ReviewOut(BaseModel):
    summary: str = Field(..., min_length=20, max_length=4000)
    allocation_findings: list[str] = Field(default_factory=list, max_length=12)
    risk_findings: list[str] = Field(default_factory=list, max_length=12)
    tax_findings: list[str] = Field(default_factory=list, max_length=12)
    recommendations: list[RecommendationOut] = Field(default_factory=list, max_length=20)
    watchlist: list[str] = Field(default_factory=list, max_length=15, description="New ideas worth research, not yet recommendations")
    data_gaps: list[str] = Field(default_factory=list, max_length=20)
