from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from rex.sim_universe.governance import compute_trust_tier_from_failures


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(payload: Any, path: str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def apply_trust_summary(
    registry: Dict[str, Any],
    summaries: List[Dict[str, Any]],
    *,
    failure_counts: Dict[str, int] | None = None,
    failure_threshold: int = 3,
) -> Dict[str, Any]:
    summary_lookup = {item["toe_candidate_id"]: item for item in summaries}
    failures = failure_counts or {}

    for entry in registry.get("toe_candidates", []):
        toe_id = entry.get("id")
        if not toe_id or toe_id not in summary_lookup:
            continue

        summary = summary_lookup[toe_id]
        trust = entry.setdefault("trust", {})
        sim_block = trust.setdefault("simuniverse", {})
        sim_block.update(
            mu_score_avg=summary["mu_score_avg"],
            faizal_score_avg=summary["faizal_score_avg"],
            undecidability_avg=summary["undecidability_avg"],
            energy_feasibility_avg=summary["energy_feasibility_avg"],
            low_trust_flag=summary["low_trust_flag"],
        )
        if "run_id" in summary:
            sim_block["last_update_run_id"] = summary["run_id"]

        current_tier = trust.get("tier", "unknown")
        failure_count = int(failures.get(toe_id, 0))
        tier = compute_trust_tier_from_failures(
            current_tier,
            failure_count,
            failure_threshold=failure_threshold,
        )
        if summary["low_trust_flag"]:
            tier = "low"
        trust["tier"] = tier

        tags = set(entry.get("sovereign_tags", []))
        if summary["low_trust_flag"]:
            tags.add("simuniverse.low_trust")
        else:
            tags.discard("simuniverse.low_trust")
        entry["sovereign_tags"] = sorted(tags)

    return registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply SimUniverse trust summaries to an ASDP registry document.",
    )
    parser.add_argument(
        "--registry",
        required=True,
        help="Path to the registry JSON file that should be updated in place.",
    )
    parser.add_argument(
        "--trust-summary",
        required=True,
        help="Path to the trust summary JSON output from the SimUniverse run.",
    )
    parser.add_argument(
        "--failure-counts",
        default=None,
        help="Optional JSON file mapping toe_candidate_id to Stage-5 gate failure counts.",
    )
    parser.add_argument(
        "--failure-threshold",
        type=int,
        default=3,
        help="Number of Stage-5 failures required before automatically demoting a TOE to low trust.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path. If omitted the registry is patched in place.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    registry = load_json(args.registry)
    summaries = load_json(args.trust_summary)
    failure_counts = load_json(args.failure_counts) if args.failure_counts else None

    updated = apply_trust_summary(
        registry,
        summaries,
        failure_counts=failure_counts,
        failure_threshold=args.failure_threshold,
    )

    destination = args.output or args.registry
    save_json(updated, destination)
    print(f"Registry updated: {destination}")


if __name__ == "__main__":
    main()
