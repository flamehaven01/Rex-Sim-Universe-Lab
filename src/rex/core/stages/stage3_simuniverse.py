from __future__ import annotations

import asyncio
from typing import Any, Dict

import httpx
import yaml

from rex.sim_universe.astro_constraints import (
    AstroConstraintConfig,
    compute_energy_feasibility,
)
from rex.sim_universe.models import (
    EnergyBudgetConfig,
    NNSLConfig,
    ResolutionConfig,
    ToeQuery,
    WorldSpec,
)
from rex.sim_universe.orchestrator import SimUniverseOrchestrator


def load_simuniverse_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def _run_simuniverse_async(payload: Dict[str, Any], config_path: str) -> Dict[str, Any]:
    cfg = load_simuniverse_config(config_path)
    sim_cfg = cfg.get("sim_universe", {})

    nnsl_ep = sim_cfg.get("nnsl_endpoint", {})
    nnsl_conf = NNSLConfig(
        base_url=nnsl_ep.get("base_url", "http://nnsl-toe-lab:8080"),
        timeout_seconds=int(nnsl_ep.get("timeout_seconds", 60)),
    )
    orchestrator = SimUniverseOrchestrator(nnsl_conf)

    astro_cfg_raw = sim_cfg.get("astro_constraints", {})
    astro_cfg = AstroConstraintConfig(
        universe_ops_upper_bound=float(
            astro_cfg_raw.get("universe_ops_upper_bound", 1e120)
        ),
        default_diag_cost_per_dim3=float(
            astro_cfg_raw.get("default_diag_cost_per_dim3", 10.0)
        ),
        default_rg_cost_per_step=float(
            astro_cfg_raw.get("default_rg_cost_per_step", 100.0)
        ),
        safety_margin=float(astro_cfg_raw.get("safety_margin", 10.0)),
    )

    world_id = "world-toy-cubitt-watson-001"
    world_spec = WorldSpec(
        world_id=world_id,
        toe_candidate_id=sim_cfg.get("worlds", {}).get(
            "default_toe_candidate", "toe_candidate_flamehaven"
        ),
        host_model=sim_cfg.get("worlds", {}).get("default_host_model", "algorithmic_host"),
        physics_modules=["lattice_hamiltonian", "rg_flow"],
        resolution=ResolutionConfig(
            lattice_spacing=sim_cfg.get("worlds", {})
            .get("default_resolution", {})
            .get("lattice_spacing", 0.1),
            time_step=sim_cfg.get("worlds", {})
            .get("default_resolution", {})
            .get("time_step", 0.01),
            max_steps=sim_cfg.get("worlds", {})
            .get("default_resolution", {})
            .get("max_steps", 1000),
        ),
        energy_budget=EnergyBudgetConfig(
            max_flops=float(
                sim_cfg.get("worlds", {})
                .get("default_energy_budget", {})
                .get("max_flops", 1e30)
            ),
            max_wallclock_seconds=float(
                sim_cfg.get("worlds", {})
                .get("default_energy_budget", {})
                .get("max_wallclock_seconds", 3600)
            ),
            notes=sim_cfg.get("worlds", {})
            .get("default_energy_budget", {})
            .get("notes", None),
        ),
        notes="Toy world combining Cubitt-style spectral gap and Watson-style RG flow.",
    )

    async with httpx.AsyncClient() as client:
        created_world_id = await orchestrator.create_world(client, world_spec)

        gap_query = ToeQuery(
            world_id=created_world_id,
            witness_id="spectral_gap_2d",
            question="gap > 0.1",
            resource_budget={
                "system_size": 6,
                "J": 1.0,
                "problem_id": 123,
                "boundary_scale": 0.05,
            },
            solver_chain=["spectral_gap"],
        )
        gap_result = await orchestrator.run_query(client, gap_query)

        rg_query = ToeQuery(
            world_id=created_world_id,
            witness_id="rg_flow_uncomputable",
            question="phase == chaotic",
            resource_budget={
                "x0": 0.2,
                "y0": 0.3,
                "r_base": 3.7,
                "program_id": 42,
                "max_depth": 256,
            },
            solver_chain=["rg_flow"],
        )
        rg_result = await orchestrator.run_query(client, rg_query)

    summary = orchestrator.summarize([gap_result, rg_result])
    summary["energy_feasibility"] = compute_energy_feasibility(
        world_spec, astro_cfg, queries=[gap_query, rg_query]
    )

    payload.setdefault("sim_universe", {})
    payload["sim_universe"]["world_spec"] = world_spec.model_dump()
    payload["sim_universe"]["queries"] = {
        "spectral_gap": gap_query.model_dump(),
        "rg_flow": rg_query.model_dump(),
    }
    payload["sim_universe"]["results"] = {
        "spectral_gap": gap_result.model_dump(),
        "rg_flow": rg_result.model_dump(),
    }
    payload["sim_universe"]["summary"] = summary

    return payload


def run_stage3_simuniverse(
    payload: Dict[str, Any], *, config_path: str = "configs/rex_simuniverse.yaml"
) -> Dict[str, Any]:
    """Synchronous wrapper for pipeline usage."""

    return asyncio.run(_run_simuniverse_async(payload, config_path))
