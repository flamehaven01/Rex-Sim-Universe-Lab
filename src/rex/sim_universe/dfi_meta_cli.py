"""DFI Meta CLI for chaining Stage-5, SimUniverse, and Omega reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Sequence

from rex.sidrce.omega_schema import OmegaAxis, OmegaReport
from rex.sidrce.omega_simuniverse_integration import (
    SIMUNIVERSE_AXIS_NAME,
    apply_simuniverse_axis,
)

from .reporting import ToeScenarioScores
from .stage5_loader import load_stage5_scores
from .trust_integration import build_toe_trust_summary, serialize_trust_summaries


@dataclass
class MetaCycleResult:
    iteration: int
    omega_total: float
    sim_axis_value: float
    level: str
    low_trust_candidates: List[str]
    omega_path: Path
    trust_path: Path


def _load_base_omega(path: Path) -> OmegaReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    axes = {
        name: (axis if isinstance(axis, OmegaAxis) else OmegaAxis(**axis))
        for name, axis in payload.get("axes", {}).items()
    }
    payload["axes"] = axes
    return OmegaReport.model_validate(payload)


def _collect_low_trust(trust_payload: Iterable[dict]) -> List[str]:
    toes = [entry["toe_candidate_id"] for entry in trust_payload if entry.get("low_trust_flag")]
    return sorted(set(toes))


def run_meta_cycles(
    *,
    scores: Sequence[ToeScenarioScores],
    base_omega: OmegaReport,
    base_run_id: str,
    out_dir: Path,
    iterations: int,
    mu_min_good: float,
    faizal_max_good: float,
    sim_weight: float,
    renormalize: bool,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    results: List[MetaCycleResult] = []
    for iteration in range(1, iterations + 1):
        iter_run_id = f"{base_run_id}-iter{iteration:02d}"
        summaries = build_toe_trust_summary(
            scores,
            mu_min_good=mu_min_good,
            faizal_max_good=faizal_max_good,
            run_id=iter_run_id,
        )
        trust_payload = serialize_trust_summaries(summaries)

        trust_path = out_dir / f"simuniverse_trust_summary_iter_{iteration:02d}.json"
        trust_path.write_text(json.dumps(trust_payload, indent=2), encoding="utf-8")

        report = apply_simuniverse_axis(
            base_omega,
            trust_payload,
            sim_weight=sim_weight,
            renormalize=renormalize,
        )
        omega_path = out_dir / f"omega_with_simuniverse_iter_{iteration:02d}.json"
        omega_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        sim_axis_value = report.axes[SIMUNIVERSE_AXIS_NAME].value
        results.append(
            MetaCycleResult(
                iteration=iteration,
                omega_total=report.omega_total,
                sim_axis_value=sim_axis_value,
                level=report.level,
                low_trust_candidates=_collect_low_trust(trust_payload),
                omega_path=omega_path,
                trust_path=trust_path,
            )
        )

    omega_totals = [result.omega_total for result in results]
    sim_values = [result.sim_axis_value for result in results]
    level_counts = Counter(result.level for result in results)
    low_trust_union = sorted({toe for result in results for toe in result.low_trust_candidates})

    omega_mean = mean(omega_totals) if omega_totals else 0.0
    sim_mean = mean(sim_values) if sim_values else 0.0
    verdict = "simulatable" if sim_mean >= 0.6 and omega_mean >= 0.82 else "obstructed"

    meta_summary = {
        "iterations": iterations,
        "omega_total_mean": omega_mean,
        "omega_total_min": min(omega_totals, default=0.0),
        "omega_total_max": max(omega_totals, default=0.0),
        "sim_axis_mean": sim_mean,
        "sim_axis_min": min(sim_values, default=0.0),
        "sim_axis_max": max(sim_values, default=0.0),
        "levels": level_counts,
        "low_trust_candidates": low_trust_union,
        "verdict": verdict,
        "iterations_detail": [
            {
                "iteration": result.iteration,
                "omega_total": result.omega_total,
                "sim_axis_value": result.sim_axis_value,
                "level": result.level,
                "omega_path": str(result.omega_path),
                "trust_path": str(result.trust_path),
            }
            for result in results
        ],
    }

    summary_path = out_dir / "dfi_meta_summary.json"
    summary_path.write_text(json.dumps(meta_summary, indent=2), encoding="utf-8")
    return meta_summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the DFI meta loop to tie Stage-5 trust data into Omega reports.",
    )
    parser.add_argument("--stage5-json", required=True, help="Path to the Stage-5 results JSON.")
    parser.add_argument("--omega-json", required=True, help="Path to the base Omega JSON.")
    parser.add_argument("--out-dir", required=True, help="Directory to write per-iteration artifacts.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=30,
        help="Number of DFI meta iterations to run (default: 30).",
    )
    parser.add_argument("--run-id", help="Optional run identifier override for iteration labeling.")
    parser.add_argument(
        "--mu-min-good",
        type=float,
        default=0.4,
        help="Minimum MUH score to avoid low-trust demotion.",
    )
    parser.add_argument(
        "--faizal-max-good",
        type=float,
        default=0.7,
        help="Maximum Faizal score tolerated before low-trust demotion.",
    )
    parser.add_argument(
        "--sim-weight",
        type=float,
        default=0.12,
        help="Weight for the simuniverse_consistency axis in Omega reports.",
    )
    parser.add_argument(
        "--no-renormalize",
        action="store_true",
        help="Skip weight renormalization when injecting the SimUniverse axis.",
    )
    args = parser.parse_args()

    stage5 = load_stage5_scores(Path(args.stage5_json))
    base_run_id = args.run_id or stage5.run_id or "stage5"
    base_omega = _load_base_omega(Path(args.omega_json))

    summary = run_meta_cycles(
        scores=stage5.scores,
        base_omega=base_omega,
        base_run_id=base_run_id,
        out_dir=Path(args.out_dir),
        iterations=args.iterations,
        mu_min_good=args.mu_min_good,
        faizal_max_good=args.faizal_max_good,
        sim_weight=args.sim_weight,
        renormalize=not args.no_renormalize,
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
