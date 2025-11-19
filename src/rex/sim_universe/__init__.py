"""REx SimUniverse Lab integration package.

Provides:
- Evidence-aware corpus models (SimUniverseCorpus v0.2)
- WorldSpec / ToeQuery / ToeResult models (re-exported from models)
- High-level orchestrator to run SimUniverse experiments via NNSL.
"""

from .models import WorldSpec, ToeQuery, ToeResult
from .corpus import SimUniverseCorpus
from .astro_constraints import AstroConstraintConfig, compute_energy_feasibility
from .reporting import (
    EvidenceLink,
    ToeScenarioScores,
    build_heatmap_matrix,
    build_toe_scenario_scores,
    compute_faizal_score,
    compute_mu_score,
    extract_rg_observables,
    print_heatmap_ascii,
    print_heatmap_with_evidence_markdown,
    format_evidence_markdown,
)
from .trust_integration import (
    ToeTrustSummary,
    build_toe_trust_summary,
    compute_trust_tier_from_failures,
    route_omega,
    serialize_trust_summaries,
    simuniverse_quality,
    update_registry_with_trust,
)
from .stage5_loader import load_stage5_scores, Stage5SimUniversePayload
from .registry import (
    SimUniverseRunCreate,
    SimUniverseRunRecord,
    SimUniverseRunRegistry,
    SimUniverseRunUpdate,
)
from .control_plane import run_stage5_for_run_id

__all__ = [
    "WorldSpec",
    "ToeQuery",
    "ToeResult",
    "SimUniverseCorpus",
    "AstroConstraintConfig",
    "compute_energy_feasibility",
    "ToeScenarioScores",
    "build_heatmap_matrix",
    "build_toe_scenario_scores",
    "compute_faizal_score",
    "compute_mu_score",
    "extract_rg_observables",
    "print_heatmap_ascii",
    "print_heatmap_with_evidence_markdown",
    "format_evidence_markdown",
    "EvidenceLink",
    "ToeTrustSummary",
    "build_toe_trust_summary",
    "serialize_trust_summaries",
    "simuniverse_quality",
    "route_omega",
    "update_registry_with_trust",
    "compute_trust_tier_from_failures",
    "load_stage5_scores",
    "Stage5SimUniversePayload",
    "SimUniverseRunCreate",
    "SimUniverseRunRecord",
    "SimUniverseRunRegistry",
    "SimUniverseRunUpdate",
    "run_stage5_for_run_id",
]
