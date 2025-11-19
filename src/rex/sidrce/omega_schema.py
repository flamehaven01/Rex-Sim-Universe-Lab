"""Pydantic models for SIDRCE Omega reports."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


class OmegaAxis(BaseModel):
    """Represents a single Omega axis entry."""

    value: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    details: Optional[dict] = None


OmegaLevel = Literal["pass", "warn", "fail"]


class OmegaReport(BaseModel):
    """Canonical structure for SIDRCE Omega reports."""

    omega_version: str
    tenant: str
    service: str
    run_id: str
    created_at: datetime
    axes: Dict[str, OmegaAxis]
    omega_total: float = Field(ge=0.0, le=1.0)
    level: OmegaLevel

