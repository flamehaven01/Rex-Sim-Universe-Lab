from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Iterable, List, Tuple


def _safe_mean(xs: Iterable[float]) -> float:
    values = list(xs)
    if not values:
        return 0.0
    return mean(values)


def summarize_undecidability_sweep(
    values: List[float | None],
    runtimes: List[float],
    failure_flags: List[bool],
) -> Tuple[float, float, float, float]:
    """Summarize a resolution sweep into an undecidability index and basic metrics.

    Args:
        values: Representative values per resolution (e.g., mean coupling or order parameter).
        runtimes: Wall-clock runtimes per resolution.
        failure_flags: True if this resolution failed (e.g., numerical breakdown).

    Returns:
        undecidability_index, time_to_partial_answer, complexity_growth, sensitivity_to_resolution
    """

    count = len(values)
    if count == 0:
        return 0.0, 0.0, 1.0, 0.0

    time_to_partial = min(runtimes) if runtimes else 0.0

    fastest = max(min(runtimes), 1e-6)
    slowest = max(runtimes) if runtimes else fastest
    complexity_growth = max(1.0, slowest / fastest)

    finite_values = [v for v in values if v is not None and math.isfinite(v)]
    if len(finite_values) >= 2:
        mean_value = _safe_mean(finite_values)
        denom = abs(mean_value) + 1e-9
        sensitivity = pstdev(finite_values) / denom
    else:
        sensitivity = 0.0

    fail_rate = sum(1 for flag in failure_flags if flag) / count

    alpha = 0.8   # weight for complexity growth
    beta = 0.6    # weight for sensitivity
    gamma = 1.0   # weight for failure rate
    delta = 1.5   # offset controlling the threshold

    score_input = (
        alpha * math.log1p(complexity_growth)
        + beta * sensitivity
        + gamma * fail_rate
        - delta
    )
    undecidability_index = 1.0 / (1.0 + math.exp(-score_input))

    return (
        float(undecidability_index),
        float(time_to_partial),
        float(complexity_growth),
        float(sensitivity),
    )
