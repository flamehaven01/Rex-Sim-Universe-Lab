"""Command line entrypoint for SIDRCE Omega + SimUniverse integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .omega_simuniverse_integration import integrate_simuniverse_into_omega


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SIDRCE Omega + SimUniverse integration CLI.",
    )
    parser.add_argument("--omega-json", required=True, help="Path to base Omega JSON report.")
    parser.add_argument(
        "--simuniverse-trust-json",
        required=True,
        help="Path to SimUniverse trust summary JSON.",
    )
    parser.add_argument("--out", required=True, help="Path to write the integrated Omega report.")
    parser.add_argument(
        "--sim-weight",
        type=float,
        default=0.12,
        help="Weight to assign to the simuniverse_consistency axis before renormalization.",
    )
    parser.add_argument(
        "--no-renormalize",
        action="store_true",
        help="Skip weight renormalization if set.",
    )
    args = parser.parse_args()

    report = integrate_simuniverse_into_omega(
        omega_path=args.omega_json,
        simuniverse_trust_path=args.simuniverse_trust_json,
        sim_weight=args.sim_weight,
        renormalize=not args.no_renormalize,
    )
    Path(args.out).write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

