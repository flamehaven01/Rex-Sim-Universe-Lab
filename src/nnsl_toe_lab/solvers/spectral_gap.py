from __future__ import annotations

import time
from typing import Dict, List

import numpy as np

from rex.sim_universe.models import ToeQuery, ToeResult, ToeResultMetrics, WorldSpec
from .base import BaseSolver
from ..semantic import SemanticField
from ..undecidability import summarize_undecidability_sweep


def parse_gap_threshold(question: str) -> float | None:
    """Parse threshold queries such as 'gap > 0.1'."""

    q = question.strip().lower()
    if "gap" in q and ">" in q:
        try:
            _, rhs = q.split(">", 1)
            return float(rhs.strip())
        except Exception:
            return None
    return None


class SpectralGapSolver(BaseSolver):
    """Simplified spectral-gap toy that avoids heavy linear algebra."""

    def __init__(self, max_spins: int = 10) -> None:
        self.max_spins = max_spins

    async def solve(self, world, query, field):  # type: ignore[override]
        rb: Dict[str, object] = query.resource_budget or {}
        base_spins = int(rb.get("system_size", 6))
        base_spins = max(3, min(self.max_spins, base_spins))

        j = float(rb.get("J", 1.0))
        problem_id = int(rb.get("problem_id", 0))
        boundary_scale = float(rb.get("boundary_scale", 0.05))
        h_over_j = 1.0 + (problem_id % 7) * 0.01
        h = h_over_j * j

        spins_list = sorted({max(3, base_spins - 1), base_spins, min(self.max_spins, base_spins + 1)})

        gaps: List[float | None] = []
        runtimes: List[float] = []
        failures: List[bool] = []

        for n in spins_list:
            t0 = time.perf_counter()
            try:
                gap_value = max(0.0, (abs(h - j) + 0.1) / (n + 1) + boundary_scale * 0.1)
                gap_value += (problem_id % 5) * 0.01
                gap_value += 0.01 * (n - base_spins)
                gaps.append(gap_value)
                failures.append(False)
            except Exception:
                gaps.append(None)
                failures.append(True)
            runtimes.append(time.perf_counter() - t0)

        u_index, time_to_partial, complexity_growth, sensitivity = summarize_undecidability_sweep(
            gaps, runtimes, failures
        )

        try:
            mid_idx = spins_list.index(base_spins)
        except ValueError:
            mid_idx = len(spins_list) // 2

        gap_mid = gaps[mid_idx]
        threshold = parse_gap_threshold(query.question)

        if gap_mid is None or not np.isfinite(gap_mid):
            status = "undecided_resource"
            approx_value = None
            confidence = 0.0
            soft = "unknown"
        else:
            approx_value = gap_mid
            status = "decided_true"
            if threshold is not None:
                soft = "true" if gap_mid > threshold else "false"
            else:
                soft = "unknown"
            confidence = 1.0

        metrics = ToeResultMetrics(
            time_to_partial_answer=time_to_partial,
            complexity_growth=complexity_growth,
            sensitivity_to_resolution=sensitivity,
        )

        return ToeResult(
            status=status,
            approx_value=approx_value,
            confidence=confidence,
            undecidability_index=u_index,
            t_soft_decision=soft,
            t_oracle_called=False,
            logs_ref=None,
            metrics=metrics,
        )


solver = SpectralGapSolver(max_spins=10)


async def solve(world: WorldSpec, query: ToeQuery, field: SemanticField) -> ToeResult:
    return await solver.solve(world, query, field)
