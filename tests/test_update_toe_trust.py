from __future__ import annotations

from scripts.update_toe_trust import apply_trust_summary


def test_apply_trust_summary_promotes_low_trust():
    registry = {
        "toe_candidates": [
            {
                "id": "toe_candidate_a",
                "label": "A",
                "sovereign_tags": [],
                "trust": {"tier": "unknown"},
            }
        ]
    }
    summaries = [
        {
            "toe_candidate_id": "toe_candidate_a",
            "runs": 1,
            "mu_score_avg": 0.2,
            "faizal_score_avg": 0.9,
            "undecidability_avg": 0.8,
            "energy_feasibility_avg": 0.1,
            "low_trust_flag": True,
            "run_id": "demo",
        }
    ]
    updated = apply_trust_summary(registry, summaries)
    toe = updated["toe_candidates"][0]
    assert toe["trust"]["tier"] == "low"
    assert "simuniverse.low_trust" in toe["sovereign_tags"]
    assert toe["trust"]["simuniverse"]["last_update_run_id"] == "demo"


def test_apply_trust_summary_uses_failure_counts():
    registry = {
        "toe_candidates": [
            {
                "id": "toe_candidate_b",
                "label": "B",
                "sovereign_tags": [],
                "trust": {"tier": "normal"},
            }
        ]
    }
    summaries = [
        {
            "toe_candidate_id": "toe_candidate_b",
            "runs": 2,
            "mu_score_avg": 0.8,
            "faizal_score_avg": 0.2,
            "undecidability_avg": 0.3,
            "energy_feasibility_avg": 0.9,
            "low_trust_flag": False,
        }
    ]
    updated = apply_trust_summary(
        registry,
        summaries,
        failure_counts={"toe_candidate_b": 5},
        failure_threshold=3,
    )
    toe = updated["toe_candidates"][0]
    assert toe["trust"]["tier"] == "low"
    assert "simuniverse.low_trust" not in toe["sovereign_tags"]
