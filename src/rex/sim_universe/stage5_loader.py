"""Helpers for loading LawBinder Stage-5 SimUniverse payloads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from .reporting import ToeScenarioScores


@dataclass
class Stage5SimUniversePayload:
    """Container for Stage-5 SimUniverse scores and metadata."""

    scores: List[ToeScenarioScores]
    run_id: str | None = None


def _coerce_float(
    record: Sequence | dict,
    key: str,
    default: float = 0.0,
    alternate_keys: Iterable[str] | None = None,
) -> float:
    value = default
    if isinstance(record, dict):
        candidates = [key, f"{key}_avg"]
        if alternate_keys:
            candidates.extend(alternate_keys)
        for candidate in candidates:
            if candidate in record:
                value = record[candidate]
                break
    try:
        return float(value)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return float(default)


def load_stage5_scores(path: str | Path) -> Stage5SimUniversePayload:
    """Load Stage-5 JSON payloads into ToeScenarioScores entries."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    run_id: str | None = None
    records: Sequence[dict]

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        run_id = payload.get("run_id") or payload.get("stage5_run_id")
        if "simuniverse_summary" in payload and isinstance(payload["simuniverse_summary"], list):
            records = payload["simuniverse_summary"]
        elif "scores" in payload and isinstance(payload["scores"], list):
            records = payload["scores"]
        else:
            raise ValueError("Stage-5 payload must contain simuniverse_summary or scores list")
    else:
        raise ValueError("Stage-5 payload must be a list or dict")

    scores: List[ToeScenarioScores] = []
    for record in records:
        scores.append(
            ToeScenarioScores(
                toe_candidate_id=str(record["toe_candidate_id"]),
                world_id=str(record.get("world_id", "unknown_world")),
                mu_score=_coerce_float(record, "mu_score"),
                faizal_score=_coerce_float(record, "faizal_score", default=1.0),
                coverage_alg=_coerce_float(record, "coverage_alg"),
                mean_undecidability_index=_coerce_float(
                    record,
                    "mean_undecidability_index",
                    alternate_keys=["undecidability_avg"],
                ),
                energy_feasibility=_coerce_float(
                    record,
                    "energy_feasibility",
                    alternate_keys=["energy_feasibility_avg"],
                ),
                rg_phase_index=_coerce_float(record, "rg_phase_index"),
                rg_halting_indicator=_coerce_float(record, "rg_halting_indicator"),
            )
        )

    return Stage5SimUniversePayload(scores=scores, run_id=run_id)
