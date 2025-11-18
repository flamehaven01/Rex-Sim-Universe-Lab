from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


HostModel = Literal["algorithmic_host", "mtoe_host", "muh_cuh_host"]
Status = Literal[
    "decided_true",
    "decided_false",
    "undecided_resource",
    "undecidable_theory",
]
SoftTruth = Literal["true", "false", "unknown"]


class ResolutionConfig(BaseModel):
    lattice_spacing: float = 0.1
    time_step: float = 0.01
    max_steps: int = 1_000


class EnergyBudgetConfig(BaseModel):
    max_flops: float = Field(..., description="Max FLOPs allowed for this world")
    max_wallclock_seconds: float = Field(..., description="Max wallclock seconds")
    notes: Optional[str] = None


class WorldSpec(BaseModel):
    world_id: str
    toe_candidate_id: str
    host_model: HostModel
    physics_modules: list[str]
    resolution: ResolutionConfig
    energy_budget: EnergyBudgetConfig
    notes: Optional[str] = None


class ToeQuery(BaseModel):
    world_id: str
    witness_id: str
    question: str
    resource_budget: dict
    solver_chain: list[str] = Field(default_factory=list)


class ToeResultMetrics(BaseModel):
    time_to_partial_answer: float
    complexity_growth: float
    sensitivity_to_resolution: float

    # RG-specific observables (optional; None for non-RG witnesses).
    rg_phase_index: Optional[float] = None
    rg_halting_indicator: Optional[float] = None


class ToeResult(BaseModel):
    status: Status
    approx_value: Optional[float] = None
    confidence: float = 0.0
    undecidability_index: float = 0.0
    t_soft_decision: SoftTruth = "unknown"
    t_oracle_called: bool = False
    logs_ref: Optional[str] = None
    metrics: ToeResultMetrics


class NNSLConfig(BaseModel):
    base_url: HttpUrl
    timeout_seconds: int = 60
