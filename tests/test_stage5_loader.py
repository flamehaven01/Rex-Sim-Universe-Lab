from __future__ import annotations

from pathlib import Path

from rex.sim_universe.stage5_loader import load_stage5_scores


def test_load_stage5_scores_detects_run_id(tmp_path: Path) -> None:
    payload = {
        "run_id": "stage5-abc",
        "simuniverse_summary": [
            {
                "toe_candidate_id": "toe_a",
                "world_id": "world-1",
                "mu_score": 0.5,
                "faizal_score": 0.4,
            }
        ],
    }
    path = tmp_path / "stage5.json"
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")

    stage5 = load_stage5_scores(path)
    assert stage5.run_id == "stage5-abc"
    assert len(stage5.scores) == 1
    assert stage5.scores[0].toe_candidate_id == "toe_a"


def test_load_stage5_scores_accepts_list(tmp_path: Path) -> None:
    payload = [
        {
            "toe_candidate_id": "toe_b",
            "world_id": "world-2",
            "mu_score_avg": 0.7,
            "faizal_score_avg": 0.3,
        }
    ]
    path = tmp_path / "stage5_list.json"
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")

    stage5 = load_stage5_scores(path)
    assert stage5.run_id is None
    assert stage5.scores[0].mu_score == 0.7
    assert stage5.scores[0].faizal_score == 0.3
