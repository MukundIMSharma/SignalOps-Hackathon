"""Investigation data shapes (see docs/CONTRACTS.md)."""
from typing import Any, Literal

from pydantic import BaseModel

Status = Literal["confirmed", "likely", "hypothesis", "unknown"]
InvestigationStatus = Literal["queued", "investigating", "partial", "awaiting_approval", "completed", "failed",
                              "cancelled"]


class Evidence(BaseModel):
    evidence_id: str
    claim: str
    status: Status
    source_system: Literal["orders", "inventory"]
    source_tool: str
    source_endpoint: str
    entity_ids: list[str]
    observed_at: str  # data clock (API as_of), not wall clock
    data: dict[str, Any]


class Finding(BaseModel):
    finding_id: str
    title: str
    summary: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    status: Status
    evidence_ids: list[str]
    confidence_explanation: str
    impact_metrics: dict[str, Any] = {}


class Action(BaseModel):
    action_id: str
    action_type: Literal["inventory_transfer", "prioritize_tickets", "draft_customer_update",
                         "create_internal_incident", "monitor_orders"]
    description: str
    inputs: dict[str, Any]
    affected_entities: list[str]
    risk_level: Literal["high", "medium", "low"]
    evidence_ids: list[str]
    expected_outcome: str
    requires_approval: bool
    approval_status: Literal["pending", "approved", "rejected", "not_required"] = "pending"


class ToolEvent(BaseModel):
    seq: int
    server: str
    tool: str
    args: dict[str, Any]
    ok: bool
    ms: int
    summary: str
