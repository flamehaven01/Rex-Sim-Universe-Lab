from __future__ import annotations

from typing import Iterable

from .models import ToeResult


def coverage_alg(results: Iterable[ToeResult]) -> float:
    results = list(results)
    if not results:
        return 0.0
    ok = sum(
        1
        for r in results
        if r.status in ("decided_true", "decided_false")
    )
    return ok / len(results)


def coverage_meta(results: Iterable[ToeResult]) -> float:
    results = list(results)
    if not results:
        return 0.0
    meta = sum(
        1
        for r in results
        if r.status == "undecidable_theory" or r.t_oracle_called
    )
    return meta / len(results)


def mean_undecidability_index(results: Iterable[ToeResult]) -> float:
    results = list(results)
    if not results:
        return 0.0
    return sum(r.undecidability_index for r in results) / len(results)
