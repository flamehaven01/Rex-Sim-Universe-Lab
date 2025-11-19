"""Minimal Prometheus exporter for SimUniverse and Omega metrics."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


app = FastAPI(title="SimUniverse Metrics Exporter")

TRUST_PATH = Path(os.environ.get("SIMUNIVERSE_TRUST_PATH", "artifacts/stage5_simuniverse/last_simuniverse_trust_summary.json"))
OMEGA_PATH = Path(os.environ.get("SIMUNIVERSE_OMEGA_PATH", "artifacts/stage5_simuniverse/omega_with_simuniverse.json"))


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _format_metric(name: str, labels: Dict[str, str] | None, value: float) -> str:
    if labels:
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}} {value}"
    return f"{name} {value}"


def render_metrics(trust_path: Path = TRUST_PATH, omega_path: Path = OMEGA_PATH) -> str:
    trust_data = _load_json(trust_path) or []
    omega_data = _load_json(omega_path)

    lines: List[str] = []
    lines.append("# HELP simuniverse_mu_score_avg Average MUH score per TOE candidate.")
    lines.append("# TYPE simuniverse_mu_score_avg gauge")
    for entry in trust_data:
        lines.append(
            _format_metric(
                "simuniverse_mu_score_avg",
                {"toe_candidate": str(entry.get("toe_candidate_id", "unknown"))},
                float(entry.get("mu_score_avg", 0.0)),
            )
        )

    lines.append("# HELP simuniverse_faizal_score_avg Average Faizal score per TOE candidate.")
    lines.append("# TYPE simuniverse_faizal_score_avg gauge")
    for entry in trust_data:
        lines.append(
            _format_metric(
                "simuniverse_faizal_score_avg",
                {"toe_candidate": str(entry.get("toe_candidate_id", "unknown"))},
                float(entry.get("faizal_score_avg", 0.0)),
            )
        )

    if omega_data:
        axes = omega_data.get("axes", {})
        sim_axis = axes.get("simuniverse_consistency")
        if sim_axis:
            lines.append("# HELP asdpi_omega_axis Omega axis values.")
            lines.append("# TYPE asdpi_omega_axis gauge")
            for axis_name, axis_payload in axes.items():
                lines.append(
                    _format_metric(
                        "asdpi_omega_axis",
                        {"axis": axis_name},
                        float(axis_payload.get("value", 0.0)),
                    )
                )
        if "omega_total" in omega_data:
            lines.append("# HELP asdpi_omega_total Omega total value.")
            lines.append("# TYPE asdpi_omega_total gauge")
            lines.append(
                _format_metric("asdpi_omega_total", None, float(omega_data.get("omega_total", 0.0)))
            )

    return "\n".join(lines) + "\n"


@app.get("/metrics", response_class=PlainTextResponse)
def metrics_endpoint() -> str:
    return render_metrics()


if __name__ == "__main__":  # pragma: no cover - manual run helper
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
