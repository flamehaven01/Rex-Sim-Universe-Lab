from __future__ import annotations

from rex.sim_universe.governance import (
    ToeTrustSummary,
    adjust_route_omega,
    build_trust_summaries,
    compute_trust_tier_from_failures,
    format_prometheus_metrics,
    serialize_trust_summaries,
    simuniverse_quality,
)
from rex.sim_universe.reporting import ToeScenarioScores


def _make_score(
    toe_id: str,
    *,
    mu: float,
    faizal: float,
    undecidability: float,
    energy: float,
) -> ToeScenarioScores:
    return ToeScenarioScores(
        toe_candidate_id=toe_id,
        world_id=f"world-{toe_id}",
        mu_score=mu,
        faizal_score=faizal,
        coverage_alg=0.5,
        mean_undecidability_index=undecidability,
        energy_feasibility=energy,
        rg_phase_index=0.2,
        rg_halting_indicator=0.3,
        evidence=[],
    )


def test_build_trust_summaries_low_trust_detection():
    scores = [
        _make_score("toe_a", mu=0.2, faizal=0.9, undecidability=0.8, energy=0.1),
        _make_score("toe_b", mu=0.8, faizal=0.2, undecidability=0.3, energy=0.8),
    ]

    summaries = build_trust_summaries(scores)
    by_id = {summary.toe_candidate_id: summary for summary in summaries}

    assert by_id["toe_a"].low_trust_flag is True
    assert by_id["toe_b"].low_trust_flag is False


def test_serialize_and_prometheus_helpers():
    summary = ToeTrustSummary(
        toe_candidate_id="toe_x",
        runs=2,
        mu_score_avg=0.4,
        faizal_score_avg=0.6,
        undecidability_avg=0.5,
        energy_feasibility_avg=0.7,
        low_trust_flag=False,
    )

    serialized = serialize_trust_summaries([summary], run_id="run-123")
    assert serialized[0]["run_id"] == "run-123"
    prom = format_prometheus_metrics([summary])
    assert "simuniverse_mu_score_avg" in prom
    assert "toe_x" in prom


def test_simuniverse_quality_and_omega_adjustment():
    quality = simuniverse_quality(
        mu_score=0.9,
        faizal_score=0.1,
        undecidability=0.6,
        energy_feasibility=0.8,
    )
    assert 0.0 <= quality <= 1.0

    omega = adjust_route_omega(base_omega=0.8, sim_quality=quality, trust_tier="normal")
    assert omega < 0.8  # tier penalty applied


def test_compute_trust_tier_from_failures():
    assert compute_trust_tier_from_failures("unknown", failure_count=0) == "normal"
    assert compute_trust_tier_from_failures("normal", failure_count=5, failure_threshold=3) == "low"
