"""CLI for syncing SimUniverse trust summaries into the ASDP registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback path
    yaml = None

from rex.sim_universe.trust_integration import update_registry_with_trust


def load_trust_summary(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    return json.loads(text)


def write_registry(path: Path, data: dict) -> None:
    if yaml is not None:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync SimUniverse trust metrics into ASDP registry files.")
    parser.add_argument("--registry", required=True, help="Path to asdp.knowledge.yaml or registry JSON.")
    parser.add_argument("--trust", required=True, help="Path to simuniverse_trust_summary.json.")
    parser.add_argument("--out", help="Optional output path. Defaults to --registry in-place update.")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    trust_path = Path(args.trust)
    out_path = Path(args.out) if args.out else registry_path

    registry_doc = load_registry(registry_path)
    trust_summary = load_trust_summary(trust_path)

    updated = update_registry_with_trust(
        registry_doc,
        trust_summary,
        fallback_run_id=trust_summary[0].get("run_id") if trust_summary else None,
    )

    write_registry(out_path, updated)
    print(f"[sync] registry updated -> {out_path}")


if __name__ == "__main__":
    main()
