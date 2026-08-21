from typing import Literal
from pydantic import BaseModel, Field


class PharmacyIssue(BaseModel):
    field: str
    reason: str
    policy: str | None = None


class PharmacyOrderItem(BaseModel):
    medication: str
    concentration: str | None = None
    pharmaceutical_form: str | None = None
    quantity: str | None = None
    external_validation_status: str | None = None


class PharmacyFulfillmentDecision(BaseModel):
    status: Literal[
        "READY_FOR_PHARMACY",
        "PHARMACY_REVIEW",
        "INSUFFICIENT_INFORMATION",
    ]
    order_items: list[PharmacyOrderItem] = Field(default_factory=list)
    blocking_issues: list[PharmacyIssue] = Field(default_factory=list)
    non_blocking_issues: list[PharmacyIssue] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
