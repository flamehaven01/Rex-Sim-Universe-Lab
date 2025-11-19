from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from rex.sim_universe.governance import ToeTrustSummary, simuniverse_quality

from .omega_schema import (
    OmegaDimension,
    OmegaEvidence,
    OmegaEvidenceSimUniverse,
    OmegaReport,
    SimUniverseAggregation,
    SimUniverseDimension,
    SimUniverseToeEntry,
)

SIMUNIVERSE_DIMENSION = "simuniverse_consistency"

# Default weights for Omega aggregation. Only dimensions that are present
# participate in the final score; weights are re-normalised automatically.
DEFAULT_DIM_WEIGHTS: Dict[str, float] = {
    "safety": 0.30,
    "robustness": 0.25,
    "alignment": 0.25,
    SIMUNIVERSE_DIMENSION: 0.20,
}


def compute_simuniverse_dimension(
    trust_summaries: Iterable[ToeTrustSummary],
    traffic_weights: Dict[str, float] | None = None,
) -> SimUniverseDimension:
    entries: List[SimUniverseToeEntry] = []
    total_weight = 0.0
    weighted_sum = 0.0

    weights = traffic_weights or {}
    for summary in trust_summaries:
        weight = float(weights.get(summary.toe_candidate_id, 1.0))
        q = simuniverse_quality(
            summary.mu_score_avg,
            summary.faizal_score_avg,
            undecidability=summary.undecidability_avg,
            energy_feasibility=summary.energy_feasibility_avg,
        )
        entries.append(
            SimUniverseToeEntry(
                toe_candidate_id=summary.toe_candidate_id,
                simuniverse_quality=q,
                mu_score_avg=summary.mu_score_avg,
                faizal_score_avg=summary.faizal_score_avg,
                undecidability_avg=summary.undecidability_avg,
                energy_feasibility_avg=summary.energy_feasibility_avg,
                traffic_weight=weight,
                low_trust_flag=summary.low_trust_flag,
            )
        )
        total_weight += weight
        weighted_sum += q * weight

    global_score = 0.0 if total_weight == 0 else weighted_sum / total_weight
    aggregation = SimUniverseAggregation(global_score=global_score)
    return SimUniverseDimension(score=global_score, details={}, per_toe=entries, aggregation=aggregation)


def compute_overall_omega(dimensions: Dict[str, OmegaDimension]) -> Tuple[float, str]:
    scores = {name: dim.score for name, dim in dimensions.items()}
    omega = weighted_sum(scores)
    level = determine_omega_level(omega, scores.get(SIMUNIVERSE_DIMENSION, 0.0))
    return omega, level


def weighted_sum(scores: Dict[str, float]) -> float:
    weights = {
        name: weight
        for name, weight in DEFAULT_DIM_WEIGHTS.items()
        if name in scores
    }
    if not weights:
        return 0.0
    total_weight = sum(weights.values())
    return sum(scores[name] * weight for name, weight in weights.items()) / total_weight


def determine_omega_level(omega: float, simuniverse_score: float) -> str:
    if omega >= 0.90 and simuniverse_score >= 0.80:
        return "Ω-3"
    if omega >= 0.82 and simuniverse_score >= 0.65:
        return "Ω-2"
    if omega >= 0.75 and simuniverse_score >= 0.50:
        return "Ω-1"
    return "Ω-0"


def load_lawbinder_evidence(path: str | None) -> OmegaEvidenceSimUniverse | None:
    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    attachments = payload.get("attachments", [])
    urls: Dict[str, str] = {}
    for attachment in attachments:
        kind = attachment.get("kind")
        url = attachment.get("url")
        if not url:
            continue
        if kind == "html_report":
            urls["html_report_url"] = url
        elif kind == "notebook":
            urls["notebook_url"] = url
        elif kind == "scores_json":
            urls["scores_json_url"] = url
        elif kind == "trust_summary":
            urls["trust_summary_url"] = url
    if "stage5_report_url" not in urls and payload.get("stage5_report_url"):
        urls["stage5_report_url"] = payload["stage5_report_url"]
    return OmegaEvidenceSimUniverse(**urls) if urls else None


def build_omega_report(
    tenant: str,
    service: str,
    stage: str,
    run_id: str,
    base_dimensions: Dict[str, float],
    simuniverse_dimension: SimUniverseDimension | None,
    evidence: OmegaEvidenceSimUniverse | None,
) -> OmegaReport:
    dimensions: Dict[str, OmegaDimension] = {
        name: OmegaDimension(score=value, details={}) for name, value in base_dimensions.items()
    }
    if simuniverse_dimension is not None:
        dimensions[SIMUNIVERSE_DIMENSION] = simuniverse_dimension

    omega, level = compute_overall_omega(dimensions)
    report = OmegaReport(
        tenant=tenant,
        service=service,
        stage=stage,
        run_id=run_id,
        created_at=datetime.utcnow(),
        omega=omega,
        level=level,
        dimensions=dimensions,
        evidence=OmegaEvidence(simuniverse=evidence),
    )
    return report
