from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from rex.sim_universe.governance import ToeTrustSummary

from sidrce.omega import (
    build_omega_report,
    compute_simuniverse_dimension,
    load_lawbinder_evidence,
)
from sidrce.omega_schema import SimUniverseDimension


def load_trust_summary(path: str | None) -> List[ToeTrustSummary]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    summaries: List[ToeTrustSummary] = []
    for item in payload:
        summaries.append(
            ToeTrustSummary(
                toe_candidate_id=item["toe_candidate_id"],
                runs=item["runs"],
                mu_score_avg=item["mu_score_avg"],
                faizal_score_avg=item["faizal_score_avg"],
                undecidability_avg=item["undecidability_avg"],
                energy_feasibility_avg=item["energy_feasibility_avg"],
                low_trust_flag=item.get("low_trust_flag", False),
            )
        )
    return summaries


def load_mapping(path: str | None) -> Dict[str, float]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(key): float(value) for key, value in data.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a SIDRCE Omega report with SimUniverse consistency.",
    )
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--base-dimensions",
        help="JSON file with baseline dimension scores, e.g. {'safety':0.9}.",
    )
    parser.add_argument(
        "--trust-summary",
        help="SimUniverse trust summary JSON from stage-5.",
    )
    parser.add_argument(
        "--traffic-weights",
        help="Optional JSON mapping toe_candidate_id to traffic weight.",
    )
    parser.add_argument(
        "--lawbinder-report",
        help="LawBinder Stage-5 report JSON containing attachment URLs.",
    )
    parser.add_argument("--output", required=True, help="Destination Omega JSON file.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    base_dimensions = load_mapping(args.base_dimensions)
    trust_summary = load_trust_summary(args.trust_summary)
    traffic_weights = load_mapping(args.traffic_weights)
    evidence = load_lawbinder_evidence(args.lawbinder_report)

    sim_dimension: SimUniverseDimension | None = None
    if trust_summary:
        sim_dimension = compute_simuniverse_dimension(trust_summary, traffic_weights)

    report = build_omega_report(
        tenant=args.tenant,
        service=args.service,
        stage=args.stage,
        run_id=args.run_id,
        base_dimensions=base_dimensions,
        simuniverse_dimension=sim_dimension,
        evidence=evidence,
    )

    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Omega report written to {destination}")


if __name__ == "__main__":
    main()
