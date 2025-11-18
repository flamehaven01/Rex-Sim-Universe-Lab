from __future__ import annotations

import math
import time
from typing import Dict, List

import numpy as np

from rex.sim_universe.models import ToeQuery, ToeResult, ToeResultMetrics, WorldSpec
from .base import BaseSolver
from ..semantic import SemanticField
from ..undecidability import summarize_undecidability_sweep


def _program_hash(program_id: int) -> float:
    """
    Deterministic hash that maps an integer program_id into (0, 1).

    This is NOT cryptographically secure; it is only used to modulate
    the RG map parameters in a reproducible way.
    """

    a = 1103515245
    c = 12345
    m = 2**31
    x = (a * (program_id & 0x7FFFFFFF) + c) % m
    return (x + 0.5) / (m + 1.0)


def rg_step(couplings: np.ndarray, program_id: int, r_base: float) -> np.ndarray:
    """
    Single RG step on a 2D coupling vector (g, h).

    Watson-inspired toy:
      - g is updated by a logistic-like chaotic map whose parameter r depends
        on program_id and the current value of h.
      - h acts as a slowly drifting phase / gate that mixes g back into h.
    """

    g, h = couplings
    p = _program_hash(program_id)

    # r in roughly [3.2, 4.0], modulated by both hash(program) and h.
    r = r_base + 0.4 * p + 0.2 * math.sin(2.0 * math.pi * h)

    # Logistic-like update with a small cross-coupling term.
    g_next = r * g * (1.0 - g) + 0.05 * math.sin(2.0 * math.pi * h)

    # h update: either slow drift or phase-mixing, depending on lowest bit.
    if program_id & 1:
        h_next = (h + 0.37) % 1.0
    else:
        h_next = (h + 0.2 * g_next + 0.11) % 1.0

    return np.array([g_next, h_next], dtype=float)


def run_rg_flow(
    x0: float,
    y0: float,
    program_id: int,
    r_base: float,
    depth: int,
) -> List[np.ndarray]:
    """
    Run the RG map for a given number of steps.

    Returns:
        List of coupling vectors along the flow.
    """

    c = np.array([x0, y0], dtype=float)
    traj = [c.copy()]
    for _ in range(depth):
        c = rg_step(c, program_id=program_id, r_base=r_base)
        traj.append(c.copy())
    return traj


def approximate_lyapunov(traj: List[np.ndarray], r_eff: float) -> float:
    """
    Very rough approximation of a Lyapunov exponent, assuming logistic-like behavior.

    For a pure logistic map x_{n+1} = r x_n (1 - x_n), the Lyapunov exponent is
      λ ≈ (1/N) Σ log |r (1 - 2 x_n)|.

    Here we only use the g-component and treat r_eff as an effective parameter.
    """

    if len(traj) < 2:
        return 0.0

    logs: List[float] = []
    for c in traj:
        g = float(c[0])
        df = r_eff * (1.0 - 2.0 * g)
        logs.append(math.log(abs(df) + 1e-9))
    return sum(logs) / len(logs)


def classify_phase(traj: List[np.ndarray], lyap: float, tol_fixed: float = 1e-4) -> str:
    """
    Classify the phase of the RG flow using trajectory stability and Lyapunov exponent.

    Heuristic:
      - 'fixed'       : late-time variance of g is tiny and lyap < 0.
      - 'chaotic'     : lyap > 0 and g visits a broad range of values.
      - 'oscillatory' : intermediate behavior.
      - 'unknown'     : everything else.
    """

    if len(traj) < 4:
        return "unknown"

    tail = traj[-32:] if len(traj) > 32 else traj
    g_tail = [float(c[0]) for c in tail]
    g_mean = sum(g_tail) / len(g_tail)
    var = sum((g - g_mean) ** 2 for g in g_tail) / len(g_tail)
    std = math.sqrt(var)

    g_min, g_max = min(g_tail), max(g_tail)
    spread = g_max - g_min

    if std < tol_fixed and lyap < 0.0:
        return "fixed"
    if lyap > 0.0 and spread > 0.3:
        return "chaotic"
    if spread > 0.1:
        return "oscillatory"
    return "unknown"


def phase_to_index(phase: str) -> float:
    """
    Map a discrete phase label to a numeric phase index.

        fixed       -> -1.0
        oscillatory ->  0.0
        chaotic     -> +1.0
        unknown     ->  0.5  (explicitly marked as ambiguous)
    """

    if phase == "fixed":
        return -1.0
    if phase == "oscillatory":
        return 0.0
    if phase == "chaotic":
        return 1.0
    return 0.5


def parse_rg_question(question: str) -> str | None:
    """
    Parse phase-based queries:
      - 'phase == fixed'
      - 'phase == chaotic'
      - 'phase == oscillatory'
    """

    q = question.strip().lower().replace(" ", "")
    if "phase==fixed" in q:
        return "fixed"
    if "phase==chaotic" in q:
        return "chaotic"
    if "phase==oscillatory" in q:
        return "oscillatory"
    return None


class RGFlowSolver(BaseSolver):
    """
    Watson-inspired RG solver with phase-aware observables.

    The solver:
      - uses a program_id to modulate the RG map,
      - performs a resolution sweep over depths,
      - approximates a Lyapunov exponent and phase label per depth,
      - computes a halting-like indicator based on phase stability,
      - maps the representative phase index to ToeResult.approx_value,
      - and reports RG observables in ToeResultMetrics.
    """

    def __init__(self, max_depth: int = 1024) -> None:
        self.max_depth = max_depth

    async def solve(self, world, query, field):  # type: ignore[override]
        rb: Dict[str, object] = query.resource_budget or {}
        x0 = float(rb.get("x0", 0.2))
        y0 = float(rb.get("y0", 0.3))
        r_base = float(rb.get("r_base", 3.7))
        program_id = int(rb.get("program_id", 42))
        max_depth = int(rb.get("max_depth", 256))
        max_depth = max(16, min(self.max_depth, max_depth))

        depths = sorted(
            set(
                [
                    max(16, max_depth // 4),
                    max(16, max_depth // 2),
                    max(16, max_depth),
                ]
            )
        )

        samples: List[float | None] = []
        runtimes: List[float] = []
        failures: List[bool] = []
        phase_by_depth: Dict[int, str] = {}
        lyap_by_depth: Dict[int, float] = {}
        phases_sequence: List[str] = []

        for depth in depths:
            start = time.perf_counter()
            try:
                traj = run_rg_flow(x0, y0, program_id, r_base, depth=depth)
                p = _program_hash(program_id)
                r_eff = r_base + 0.3 * p
                lyap = approximate_lyapunov(traj, r_eff=r_eff)
                phase = classify_phase(traj, lyap)

                phase_by_depth[depth] = phase
                lyap_by_depth[depth] = lyap
                phases_sequence.append(phase)

                tail = traj[-20:] if len(traj) > 20 else traj
                g_tail = [float(c[0]) for c in tail]
                value = float(sum(g_tail) / len(g_tail))
                failed = False
            except Exception:
                phase = "unknown"
                lyap = 0.0
                phase_by_depth[depth] = phase
                lyap_by_depth[depth] = lyap
                phases_sequence.append(phase)

                value = None
                failed = True

            elapsed = time.perf_counter() - start

            samples.append(value)
            runtimes.append(elapsed)
            failures.append(failed)

        (
            undecidability_index,
            time_to_partial,
            complexity_growth,
            sensitivity,
        ) = summarize_undecidability_sweep(samples, runtimes, failures)

        mid_depth = depths[len(depths) // 2]
        representative_phase = phase_by_depth.get(mid_depth, "unknown")
        phase_index = phase_to_index(representative_phase)

        if all(p == representative_phase and p != "unknown" for p in phases_sequence):
            halting_indicator = 1.0
        else:
            non_unknown = [p for p in phases_sequence if p != "unknown"]
            if not non_unknown:
                halting_indicator = 0.0
            else:
                matches = sum(1 for p in non_unknown if p == representative_phase)
                halting_indicator = matches / len(non_unknown)

        target_phase = parse_rg_question(query.question)

        if all(failures):
            status = "undecided_resource"
            approx_value = None
            confidence = 0.0
            soft_truth = "unknown"
        else:
            approx_value = phase_index
            status = "decided_true"
            if target_phase is None:
                soft_truth = "unknown"
            else:
                soft_truth = "true" if representative_phase == target_phase else "false"
            confidence = 0.8

        metrics = ToeResultMetrics(
            time_to_partial_answer=time_to_partial,
            complexity_growth=complexity_growth,
            sensitivity_to_resolution=sensitivity,
            rg_phase_index=phase_index,
            rg_halting_indicator=halting_indicator,
        )

        t_oracle = False

        return ToeResult(
            status=status,
            approx_value=approx_value,
            confidence=confidence,
            undecidability_index=undecidability_index,
            t_soft_decision=soft_truth,
            t_oracle_called=t_oracle,
            logs_ref=None,
            metrics=metrics,
        )


solver = RGFlowSolver(max_depth=1024)


async def solve(world: WorldSpec, query: ToeQuery, field: SemanticField) -> ToeResult:
    return await solver.solve(world, query, field)
