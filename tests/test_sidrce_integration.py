from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rex.sidrce.omega_simuniverse_integration import (
    SIMUNIVERSE_AXIS_NAME,
    apply_simuniverse_axis,
    compute_simuniverse_consistency,
    integrate_simuniverse_into_omega,
)
from rex.sidrce.omega_schema import OmegaAxis, OmegaReport


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_compute_simuniverse_consistency_scales_with_scores() -> None:
    summary = [
        {
            "toe_candidate_id": "toe_a",
            "mu_score_avg": 0.8,
            "faizal_score_avg": 0.2,
            "undecidability_avg": 0.6,
            "energy_feasibility_avg": 0.9,
        },
        {
            "toe_candidate_id": "toe_b",
            "mu_score_avg": 0.6,
            "faizal_score_avg": 0.5,
            "undecidability_avg": 0.4,
            "energy_feasibility_avg": 0.8,
        },
    ]

    stats = compute_simuniverse_consistency(summary)
    expected = 0.7 * ((0.8 + 0.6) / 2) + 0.3 * (1 - ((0.2 + 0.5) / 2))
    assert stats["value"] == expected
    assert stats["mu_score_avg_global"] == (0.8 + 0.6) / 2
    assert stats["faizal_score_avg_global"] == (0.2 + 0.5) / 2
    assert stats["undecidability_avg_global"] == (0.6 + 0.4) / 2
    assert stats["energy_feasibility_avg_global"] == (0.9 + 0.8) / 2


def test_integrate_simuniverse_into_omega(tmp_path: Path) -> None:
    base_report = OmegaReport(
        omega_version="8.1",
        tenant="flamehaven",
        service="rex-engine",
        run_id="run-123",
        created_at=datetime.utcnow(),
        axes={
            "coverage": OmegaAxis(value=0.9, weight=0.25),
            "robustness": OmegaAxis(value=0.85, weight=0.25),
            "safety": OmegaAxis(value=0.88, weight=0.25),
            "finops": OmegaAxis(value=0.86, weight=0.25),
        },
        omega_total=0.0,
        level="fail",
    )
    omega_path = tmp_path / "omega.json"
    omega_path.write_text(
        json.dumps(base_report.model_dump(), default=str),
        encoding="utf-8",
    )

    sim_summary = [
        {
            "toe_candidate_id": "toe_a",
            "mu_score_avg": 0.75,
            "faizal_score_avg": 0.3,
            "undecidability_avg": 0.5,
            "energy_feasibility_avg": 0.95,
            "low_trust_flag": False,
            "high_trust_flag": True,
        },
        {
            "toe_candidate_id": "toe_b",
            "mu_score_avg": 0.65,
            "faizal_score_avg": 0.4,
            "undecidability_avg": 0.55,
            "energy_feasibility_avg": 0.85,
            "low_trust_flag": True,
        },
    ]
    trust_path = tmp_path / "trust.json"
    _write_json(trust_path, sim_summary)

    report = integrate_simuniverse_into_omega(
        omega_path=str(omega_path),
        simuniverse_trust_path=str(trust_path),
    )

    assert SIMUNIVERSE_AXIS_NAME in report.axes
    axis = report.axes[SIMUNIVERSE_AXIS_NAME]
    assert 0.0 <= axis.value <= 1.0
    assert abs(sum(a.weight for a in report.axes.values()) - 1.0) < 1e-9
    assert report.omega_total == sum(a.value * a.weight for a in report.axes.values())
    assert report.level in {"pass", "warn", "fail"}
    assert axis.details["toe_trust_tiers"]["toe_a"] == "high"
    assert axis.details["toe_trust_tiers"]["toe_b"] == "low"


def test_apply_simuniverse_axis_in_memory() -> None:
    base_report = OmegaReport(
        omega_version="8.2",
        tenant="flamehaven",
        service="rex-engine",
        run_id="run-xyz",
        created_at=datetime.utcnow(),
        axes={
            "coverage": OmegaAxis(value=0.9, weight=0.5),
            "robustness": OmegaAxis(value=0.85, weight=0.5),
        },
        omega_total=0.0,
        level="fail",
    )
    trust_summary = [
        {
            "toe_candidate_id": "toe_a",
            "mu_score_avg": 0.8,
            "faizal_score_avg": 0.3,
            "undecidability_avg": 0.5,
            "energy_feasibility_avg": 0.9,
        }
    ]

    report = apply_simuniverse_axis(
        base_report,
        trust_summary,
        sim_weight=0.2,
        renormalize=False,
    )

    assert SIMUNIVERSE_AXIS_NAME in report.axes
    assert abs(sum(axis.weight for axis in report.axes.values()) - 1.2) < 1e-9
    assert report.axes[SIMUNIVERSE_AXIS_NAME].weight == 0.2

