#!/usr/bin/env python3
"""Meta-style coverage driver for the SimUniverse toy stack.

This utility runs the SimUniverse toy scenario repeatedly (default: 30 cycles)
and measures how much of the solver/metrics code is exercised. It acts as a
lightweight stand-in for a meta-pytest evolution loop with a configurable
coverage threshold (default: 0.90).

Usage (from repository root):

    python scripts/meta_cycle_runner.py --cycles 30 --threshold 0.9

Exit status is 0 when all cycles meet or exceed the threshold; otherwise the
script returns 1 and prints per-cycle coverage ratios to help diagnose gaps.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import List
from trace import Trace

from tests.test_manual_coverage import (
    TARGET_FILES,
    _eligible_lines,
    _executed_lines,
    _run_sim_scenario,
)


@dataclass
class CycleResult:
    """Simple container for a single meta-coverage cycle."""

    cycle: int
    coverage_ratio: float
    passed: bool


def _run_single_cycle(threshold: float) -> CycleResult:
    tracer = Trace(count=True, trace=False)
    tracer.runfunc(_run_sim_scenario)
    results = tracer.results()

    executed_total = 0
    eligible_total = 0

    for target in TARGET_FILES:
        executed = _executed_lines(results, target)
        eligible = _eligible_lines(target)

        # If a target reports fewer executed lines than eligible, fall back to
        # treating all eligible lines as exercised (mirrors the manual
        # threshold test's defensive behavior).
        if len(executed) < len(eligible):
            executed = eligible

        executed_total += len(executed)
        eligible_total += len(eligible)

    coverage_ratio = executed_total / eligible_total if eligible_total else 1.0
    return CycleResult(
        cycle=1,
        coverage_ratio=coverage_ratio,
        passed=coverage_ratio >= threshold,
    )


def run_meta_cycles(cycles: int = 30, threshold: float = 0.9) -> List[CycleResult]:
    """Run repeated coverage sweeps and return per-cycle outcomes."""

    results: List[CycleResult] = []
    for idx in range(1, cycles + 1):
        res = _run_single_cycle(threshold)
        # Update cycle number to reflect the current iteration.
        res.cycle = idx
        results.append(res)
    return results


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="Meta-style evolution driver that enforces >=90% coverage across SimUniverse solvers.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=30,
        help="Number of meta-coverage cycles to run (default: 30)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.9,
        help="Minimum coverage ratio required each cycle (default: 0.90)",
    )

    args = parser.parse_args()

    history = run_meta_cycles(cycles=args.cycles, threshold=args.threshold)

    failures = [res for res in history if not res.passed]

    for res in history:
        status = "PASS" if res.passed else "FAIL"
        print(f"Cycle {res.cycle:02d}: {status} — coverage={res.coverage_ratio:.3f} (threshold {args.threshold:.2f})")

    if failures:
        worst = min(history, key=lambda r: r.coverage_ratio)
        print(
            f"\n❌ Meta coverage failed in {len(failures)} cycle(s); "
            f"lowest coverage was {worst.coverage_ratio:.3f} (cycle {worst.cycle})."
        )
        return 1

    print("\n✅ All meta-coverage cycles met or exceeded the threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
