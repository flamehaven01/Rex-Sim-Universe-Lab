from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dfi_meta_cli.py"


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("dfi_meta_cli", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


def test_meta_tensor_weights_sum():
    mod = _load_cli_module()
    tensor = mod.MetaCognitiveTensor(awareness=0.5, reflection=0.5, adaptation=0.5, emergence=0.5, quantum_coherence=0.5)
    score = tensor.compute_omega()
    # 0.30 + 0.25 + 0.20 + 0.15 + 0.10 = 1.0 total weight
    assert 0.4 <= score <= 1.0


def test_meta_check_runs_at_depth_one():
    mod = _load_cli_module()
    cli = mod.DFIMetaCLI()
    results = cli.meta_check(depth=1)
    assert "system_coherence" in results
    assert isinstance(results["meta_layers"], list)


def test_evolve_short_circuit_event_loop():
    mod = _load_cli_module()
    cli = mod.DFIMetaCLI()

    async def run_once():
        return await cli.evolve(cycles=1, threshold=0.0)

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(run_once())
    finally:
        loop.close()

    assert "final_omega" in result
    assert result["cycles"], "At least one cycle result should be present"
