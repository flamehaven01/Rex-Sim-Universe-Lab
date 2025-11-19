from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_metrics_exporter_outputs_metrics(tmp_path: Path) -> None:
    trust_path = tmp_path / "trust.json"
    omega_path = tmp_path / "omega.json"
    trust_path.write_text(
        json.dumps(
            [
                {
                    "toe_candidate_id": "toe_a",
                    "mu_score_avg": 0.8,
                    "faizal_score_avg": 0.2,
                }
            ]
        ),
        encoding="utf-8",
    )
    omega_path.write_text(
        json.dumps(
            {
                "axes": {
                    "coverage": {"value": 0.9},
                    "simuniverse_consistency": {"value": 0.75},
                },
                "omega_total": 0.88,
            }
        ),
        encoding="utf-8",
    )

    exporter = importlib.import_module("rex.sim_universe.metrics_exporter")
    exporter = importlib.reload(exporter)
    body = exporter.render_metrics(trust_path, omega_path)
    assert "simuniverse_mu_score_avg" in body
    assert "asdpi_omega_total" in body
