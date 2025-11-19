from __future__ import annotations

from rex.core.stages.stage3_simuniverse import run_stage3_simuniverse

STAGES = [
    ("stage3_simuniverse", run_stage3_simuniverse),
]


def run_pipeline(initial_payload: dict) -> dict:
    payload = dict(initial_payload)
    for name, fn in STAGES:
        payload = fn(payload)
    return payload


if __name__ == "__main__":
    example_payload = {"input": "toe-sim test"}
    final_payload = run_pipeline(example_payload)
    print(final_payload.get("sim_universe", {}).get("summary"))
