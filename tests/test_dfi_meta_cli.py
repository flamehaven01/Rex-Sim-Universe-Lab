from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rex.sidrce.omega_schema import OmegaAxis, OmegaReport
from rex.sim_universe.dfi_meta_cli import run_meta_cycles
from rex.sim_universe.reporting import ToeScenarioScores


def _base_omega() -> OmegaReport:
    return OmegaReport(
        omega_version="8.1",
        tenant="flamehaven",
        service="rex-engine",
        run_id="run-base",
        created_at=datetime(2025, 1, 1),
        axes={
            "coverage": OmegaAxis(value=0.9, weight=0.25),
            "robustness": OmegaAxis(value=0.85, weight=0.25),
            "safety": OmegaAxis(value=0.87, weight=0.25),
            "finops": OmegaAxis(value=0.84, weight=0.25),
        },
        omega_total=0.0,
        level="fail",
    )


def _scores() -> list[ToeScenarioScores]:
    return [
        ToeScenarioScores(
            toe_candidate_id="toe_high",
            world_id="world-1",
            mu_score=0.8,
            faizal_score=0.2,
        ),
        ToeScenarioScores(
            toe_candidate_id="toe_low",
            world_id="world-2",
            mu_score=0.2,
            faizal_score=0.8,
        ),
    ]


def test_run_meta_cycles_writes_outputs(tmp_path: Path) -> None:
    summary = run_meta_cycles(
        scores=_scores(),
        base_omega=_base_omega(),
        base_run_id="demo",
        out_dir=tmp_path,
        iterations=3,
        mu_min_good=0.4,
        faizal_max_good=0.7,
        sim_weight=0.12,
        renormalize=True,
    )

    assert summary["iterations"] == 3
    assert summary["verdict"] in {"simulatable", "obstructed"}
    assert (tmp_path / "dfi_meta_summary.json").exists()
    assert (tmp_path / "simuniverse_trust_summary_iter_01.json").exists()
    assert (tmp_path / "omega_with_simuniverse_iter_01.json").exists()
    assert len(summary["iterations_detail"]) == 3
