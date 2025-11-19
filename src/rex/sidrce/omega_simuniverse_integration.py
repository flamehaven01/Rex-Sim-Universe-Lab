"""Utilities for merging SimUniverse metrics into SIDRCE Omega reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

from .omega_schema import OmegaAxis, OmegaReport


SIMUNIVERSE_AXIS_NAME = "simuniverse_consistency"


def load_simuniverse_trust_summary(path: str) -> List[dict]:
    """Load the SimUniverse trust summary JSON as a list of dicts."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("SimUniverse trust summary must be a list")
    return data


def _safe_average(items: Iterable[Mapping[str, float]], key: str, default: float = 0.0) -> float:
    values = [float(entry.get(key, default)) for entry in items]
    if not values:
        return default
    return sum(values) / len(values)


def compute_simuniverse_consistency(trust_summary: List[Mapping[str, float]]) -> Dict[str, float]:
    """Aggregate per-TOE SimUniverse metrics into a scalar axis value."""

    if not trust_summary:
        return {
            "value": 0.0,
            "mu_score_avg_global": 0.0,
            "faizal_score_avg_global": 1.0,
            "undecidability_avg_global": 0.0,
            "energy_feasibility_avg_global": 0.0,
        }

    mu_avg = _safe_average(trust_summary, "mu_score_avg")
    faizal_avg = _safe_average(trust_summary, "faizal_score_avg", default=1.0)
    u_avg = _safe_average(trust_summary, "undecidability_avg")
    energy_avg = _safe_average(trust_summary, "energy_feasibility_avg")

    sim_q = 0.7 * mu_avg + 0.3 * (1.0 - faizal_avg)
    sim_value = max(0.0, min(1.0, sim_q))

    return {
        "value": sim_value,
        "mu_score_avg_global": mu_avg,
        "faizal_score_avg_global": faizal_avg,
        "undecidability_avg_global": u_avg,
        "energy_feasibility_avg_global": energy_avg,
    }


def _build_trust_tiers(trust_summary: List[Mapping[str, float]]) -> Dict[str, str]:
    tiers: Dict[str, str] = {}
    for entry in trust_summary:
        toe_id = str(entry.get("toe_candidate_id", "unknown_toe"))
        if entry.get("high_trust_flag"):
            tier = "high"
        elif entry.get("low_trust_flag"):
            tier = "low"
        else:
            tier = "normal"
        tiers[toe_id] = tier
    return tiers


def _evaluate_omega_level(omega_total: float, sim_value: float) -> str:
    if omega_total >= 0.85 and sim_value >= 0.75:
        return "pass"
    if omega_total >= 0.82 and sim_value >= 0.60:
        return "warn"
    return "fail"


def _normalize_trust_summary(
    trust_summary: Sequence[Mapping[str, float] | object]
) -> List[Mapping[str, float]]:
    normalized: List[Mapping[str, float]] = []
    for entry in trust_summary:
        if hasattr(entry, "to_payload"):
            payload = entry.to_payload()  # type: ignore[attr-defined]
        else:
            payload = dict(entry)  # type: ignore[arg-type]
        normalized.append(payload)
    return normalized


def apply_simuniverse_axis(
    omega: OmegaReport,
    trust_summary: Sequence[Mapping[str, float] | object],
    *,
    sim_weight: float = 0.12,
    renormalize: bool = True,
) -> OmegaReport:
    """Return a copy of ``omega`` enriched with the SimUniverse axis."""

    report = OmegaReport.model_validate(omega.model_dump())
    normalized = _normalize_trust_summary(trust_summary)
    sim_stats = compute_simuniverse_consistency(normalized)

    axes: Dict[str, OmegaAxis] = {}
    for axis_name, axis_value in getattr(report, "axes", {}).items():
        if isinstance(axis_value, OmegaAxis):
            axes[axis_name] = axis_value
        else:
            axes[axis_name] = OmegaAxis(**axis_value)

    axes[SIMUNIVERSE_AXIS_NAME] = OmegaAxis(
        value=sim_stats["value"],
        weight=sim_weight,
        details={
            "mu_score_avg_global": sim_stats["mu_score_avg_global"],
            "faizal_score_avg_global": sim_stats["faizal_score_avg_global"],
            "undecidability_avg_global": sim_stats["undecidability_avg_global"],
            "energy_feasibility_avg_global": sim_stats["energy_feasibility_avg_global"],
            "toe_trust_tiers": _build_trust_tiers(normalized),
        },
    )

    if renormalize:
        total_weight = sum(axis.weight for axis in axes.values())
        if total_weight > 0:
            for axis in axes.values():
                axis.weight = axis.weight / total_weight

    omega_value = sum(axis.value * axis.weight for axis in axes.values())
    report.axes = axes
    report.omega_total = max(0.0, min(1.0, omega_value))

    sim_value = axes[SIMUNIVERSE_AXIS_NAME].value
    report.level = _evaluate_omega_level(report.omega_total, sim_value)
    return report


def integrate_simuniverse_into_omega(
    omega_path: str,
    simuniverse_trust_path: str,
    sim_weight: float = 0.12,
    renormalize: bool = True,
) -> OmegaReport:
    """Merge SimUniverse metrics into an Omega report and recompute totals."""

    omega_payload = json.loads(Path(omega_path).read_text(encoding="utf-8"))
    omega = OmegaReport.model_validate(omega_payload)
    trust_summary = load_simuniverse_trust_summary(simuniverse_trust_path)
    return apply_simuniverse_axis(
        omega,
        trust_summary,
        sim_weight=sim_weight,
        renormalize=renormalize,
    )

