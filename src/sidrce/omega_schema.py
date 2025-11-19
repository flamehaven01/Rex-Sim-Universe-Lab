from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class SimUniverseToeEntry(BaseModel):
    toe_candidate_id: str
    simuniverse_quality: float
    mu_score_avg: float
    faizal_score_avg: float
    undecidability_avg: float
    energy_feasibility_avg: float
    traffic_weight: float = 1.0
    low_trust_flag: bool = False


class SimUniverseAggregation(BaseModel):
    method: str = "traffic_weighted_mean"
    traffic_window: str = "7d"
    global_score: float


class OmegaDimension(BaseModel):
    score: float
    details: Dict[str, object] = {}


class SimUniverseDimension(OmegaDimension):
    per_toe: List[SimUniverseToeEntry]
    aggregation: SimUniverseAggregation


class OmegaEvidenceSimUniverse(BaseModel):
    stage5_report_url: Optional[HttpUrl] = None
    html_report_url: Optional[HttpUrl] = None
    notebook_url: Optional[HttpUrl] = None
    scores_json_url: Optional[HttpUrl] = None
    trust_summary_url: Optional[HttpUrl] = None


class OmegaEvidence(BaseModel):
    safety: Optional[Dict[str, object]] = None
    robustness: Optional[Dict[str, object]] = None
    alignment: Optional[Dict[str, object]] = None
    simuniverse: Optional[OmegaEvidenceSimUniverse] = None


class OmegaReport(BaseModel):
    tenant: str
    service: str
    stage: str
    run_id: str
    created_at: datetime
    omega: float
    level: str
    dimensions: Dict[str, OmegaDimension]
    evidence: OmegaEvidence
