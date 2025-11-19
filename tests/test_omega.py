from __future__ import annotations

import json
from pathlib import Path

from rex.sim_universe.governance import ToeTrustSummary

from sidrce.omega import (
    SIMUNIVERSE_DIMENSION,
    build_omega_report,
    compute_overall_omega,
    compute_simuniverse_dimension,
    determine_omega_level,
)
from sidrce.omega_schema import OmegaDimension


def _summary(toe: str, mu: float, faizal: float, u: float, energy: float, low=False) -> ToeTrustSummary:
    return ToeTrustSummary(
        toe_candidate_id=toe,
        runs=2,
        mu_score_avg=mu,
        faizal_score_avg=faizal,
        undecidability_avg=u,
        energy_feasibility_avg=energy,
        low_trust_flag=low,
    )


def test_compute_simuniverse_dimension_weights():
    summaries = [
        _summary("toe_a", mu=0.9, faizal=0.1, u=0.6, energy=0.7),
        _summary("toe_b", mu=0.2, faizal=0.8, u=0.9, energy=0.2, low=True),
    ]
    weights = {"toe_a": 3.0, "toe_b": 1.0}
    dimension = compute_simuniverse_dimension(summaries, weights)
    assert len(dimension.per_toe) == 2
    assert dimension.aggregation.global_score >= dimension.per_toe[1].simuniverse_quality


def test_compute_overall_omega_and_levels():
    dims = {
        "safety": OmegaDimension(score=0.9, details={}),
        "robustness": OmegaDimension(score=0.85, details={}),
        SIMUNIVERSE_DIMENSION: OmegaDimension(score=0.8, details={}),
    }
    omega, level = compute_overall_omega(dims)
    assert 0.0 <= omega <= 1.0
    assert level in {"Ω-3", "Ω-2", "Ω-1", "Ω-0"}

    assert determine_omega_level(0.91, 0.81) == "Ω-3"
    assert determine_omega_level(0.83, 0.7) == "Ω-2"
    assert determine_omega_level(0.76, 0.5) == "Ω-1"
    assert determine_omega_level(0.6, 0.2) == "Ω-0"


def test_build_omega_report(tmp_path: Path):
    summaries = [_summary("toe_a", 0.8, 0.2, 0.6, 0.5)]
    sim_dim = compute_simuniverse_dimension(summaries, {})
    report = build_omega_report(
        tenant="tenant",
        service="service",
        stage="stage5",
        run_id="run-1",
        base_dimensions={"safety": 0.9},
        simuniverse_dimension=sim_dim,
        evidence=None,
    )
    output = tmp_path / "omega.json"
    output.write_text(json.dumps(report.model_dump(), indent=2, default=str))
    data = json.loads(output.read_text())
    assert data["dimensions"][SIMUNIVERSE_DIMENSION]["score"] == sim_dim.score
