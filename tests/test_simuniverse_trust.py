from __future__ import annotations

from rex.sim_universe.reporting import ToeScenarioScores
from rex.sim_universe.trust_integration import (
    ToeTrustSummary,
    build_toe_trust_summary,
    compute_trust_tier_from_failures,
    route_omega,
    simuniverse_quality,
    update_registry_with_trust,
)


def _scenario(**overrides: float | str) -> ToeScenarioScores:
    base = dict(
        toe_candidate_id="toe_a",
        world_id="world-1",
        mu_score=0.5,
        faizal_score=0.5,
        coverage_alg=0.0,
        mean_undecidability_index=0.5,
        energy_feasibility=0.5,
        rg_phase_index=0.0,
        rg_halting_indicator=0.0,
    )
    base.update(overrides)
    return ToeScenarioScores(**base)


def test_build_toe_trust_summary_flags_low_trust() -> None:
    scores = [
        _scenario(toe_candidate_id="toe_low", mu_score=0.2, faizal_score=0.9, mean_undecidability_index=0.8),
        _scenario(
            toe_candidate_id="toe_low",
            world_id="world-2",
            mu_score=0.25,
            faizal_score=0.85,
            mean_undecidability_index=0.7,
        ),
        _scenario(toe_candidate_id="toe_high", mu_score=0.8, faizal_score=0.2, mean_undecidability_index=0.3),
    ]

    summaries = build_toe_trust_summary(scores, mu_min_good=0.4, faizal_max_good=0.7, run_id="run-abc")
    summary_by_toe = {summary.toe_candidate_id: summary for summary in summaries}

    assert summary_by_toe["toe_low"].low_trust_flag is True
    assert summary_by_toe["toe_low"].runs == 2
    assert summary_by_toe["toe_low"].run_id == "run-abc"
    assert summary_by_toe["toe_high"].low_trust_flag is False


def test_update_registry_with_trust_sets_tags_and_tier() -> None:
    registry = {
        "toe_candidates": [
            {"id": "toe_low", "sovereign_tags": [], "trust": {"tier": "unknown"}},
            {"id": "toe_high", "trust": {"tier": "high", "simuniverse": {}}},
        ]
    }
    summaries = [
        ToeTrustSummary(
            toe_candidate_id="toe_low",
            runs=2,
            mu_score_avg=0.2,
            faizal_score_avg=0.9,
            undecidability_avg=0.7,
            energy_feasibility_avg=0.4,
            low_trust_flag=True,
            run_id="run-1",
        ),
        ToeTrustSummary(
            toe_candidate_id="toe_high",
            runs=1,
            mu_score_avg=0.8,
            faizal_score_avg=0.2,
            undecidability_avg=0.3,
            energy_feasibility_avg=0.8,
            low_trust_flag=False,
            run_id="run-1",
        ),
    ]

    updated = update_registry_with_trust(registry, summaries)
    low_entry = updated["toe_candidates"][0]
    high_entry = updated["toe_candidates"][1]

    assert low_entry["trust"]["tier"] == "low"
    assert "simuniverse.low_trust" in low_entry["sovereign_tags"]
    assert low_entry["trust"]["simuniverse"]["low_trust_flag"] is True

    assert high_entry["trust"]["tier"] == "high"
    assert "simuniverse.low_trust" not in high_entry.get("sovereign_tags", [])


def test_simuniverse_quality_and_route_omega() -> None:
    sim_q = simuniverse_quality(mu_score=0.9, faizal_score=0.1)
    assert 0.0 <= sim_q <= 1.0

    routed = route_omega(base_omega=0.85, sim_q=sim_q, trust_tier="low")
    assert routed < 0.85  # penalized by low trust tier


def test_compute_trust_tier_from_failures_threshold() -> None:
    assert compute_trust_tier_from_failures("unknown", failure_count=0) == "normal"
    assert compute_trust_tier_from_failures("normal", failure_count=5, failure_threshold=3) == "low"
