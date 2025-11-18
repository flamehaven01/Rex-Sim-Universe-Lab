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
]
