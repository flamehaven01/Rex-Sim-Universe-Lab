from __future__ import annotations

import argparse
import json
from pathlib import Path

from rex.sim_universe.stage5_loader import load_stage5_scores
from rex.sim_universe.trust_integration import (
    build_toe_trust_summary,
    serialize_trust_summaries,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build per-TOE SimUniverse trust summaries from Stage-5 results."
    )
    parser.add_argument("--stage5-json", required=True, help="Path to the Stage-5 results JSON.")
    parser.add_argument("--out", required=True, help="Path to write the trust summary JSON.")
    parser.add_argument("--run-id", help="Optional run identifier to embed in the trust summary.")
    parser.add_argument(
        "--mu-min-good",
        type=float,
        default=0.4,
        help="Minimum MUH score to avoid a low-trust designation.",
    )
    parser.add_argument(
        "--faizal-max-good",
        type=float,
        default=0.7,
        help="Maximum Faizal score to avoid a low-trust designation.",
    )
    args = parser.parse_args()

    stage5_path = Path(args.stage5_json)
    stage5_payload = load_stage5_scores(stage5_path)
    scores = stage5_payload.scores
    run_id = args.run_id or stage5_payload.run_id
    summaries = build_toe_trust_summary(
        scores,
        mu_min_good=args.mu_min_good,
        faizal_max_good=args.faizal_max_good,
        run_id=run_id,
    )
    payload = serialize_trust_summaries(summaries)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
