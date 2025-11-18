from __future__ import annotations

import asyncio
import json
from typing import Dict, List

import httpx
import yaml

from rex.sim_universe.astro_constraints import AstroConstraintConfig, compute_energy_feasibility
from rex.sim_universe.corpus import SimUniverseCorpus
from rex.sim_universe.models import (
    EnergyBudgetConfig,
    NNSLConfig,
    ResolutionConfig,
    ToeQuery,
    WorldSpec,
)
from rex.sim_universe.orchestrator import SimUniverseOrchestrator
from rex.sim_universe.reporting import (
    ToeScenarioScores,
    build_heatmap_matrix,
    build_toe_scenario_scores,
    print_heatmap_ascii,
)


def load_simuniverse_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_corpus(path: str) -> SimUniverseCorpus:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return SimUniverseCorpus(**data)


async def run_single_scenario(
    nnsl_conf: NNSLConfig,
    astro_cfg: AstroConstraintConfig,
    corpus: SimUniverseCorpus,
    toe_candidate_id: str,
    world_index: int,
    world_template: dict,
) -> ToeScenarioScores:
    orchestrator = SimUniverseOrchestrator(nnsl_conf)

    world_id = f"world-{toe_candidate_id}-{world_index:03d}"
    world_spec = WorldSpec(
        world_id=world_id,
        toe_candidate_id=toe_candidate_id,
        host_model=world_template.get("host_model", "algorithmic_host"),
        physics_modules=world_template.get(
            "physics_modules", ["lattice_hamiltonian", "rg_flow"]
        ),
        resolution=ResolutionConfig(
            lattice_spacing=world_template["resolution"]["lattice_spacing"],
            time_step=world_template["resolution"]["time_step"],
            max_steps=world_template["resolution"]["max_steps"],
        ),
        energy_budget=EnergyBudgetConfig(
            max_flops=world_template["energy_budget"]["max_flops"],
            max_wallclock_seconds=world_template["energy_budget"][
                "max_wallclock_seconds"
            ],
            notes=world_template["energy_budget"].get("notes"),
        ),
        notes=world_template.get("notes", ""),
    )

    async with httpx.AsyncClient() as client:
        created_world_id = await orchestrator.create_world(client, world_spec)

        gap_query = ToeQuery(
            world_id=created_world_id,
            witness_id="spectral_gap_2d",
            question="gap > 0.1",
            resource_budget={
                "system_size": world_template.get("gap_system_size", 6),
                "J": 1.0,
                "problem_id": world_template.get("problem_id", 0),
                "boundary_scale": world_template.get("boundary_scale", 0.05),
            },
            solver_chain=["spectral_gap"],
        )
        gap_result = await orchestrator.run_query(client, gap_query)

        rg_query = ToeQuery(
            world_id=created_world_id,
            witness_id="rg_flow_uncomputable",
            question=world_template.get("rg_question", "phase == chaotic"),
            resource_budget={
                "x0": world_template.get("rg_x0", 0.2),
                "y0": world_template.get("rg_y0", 0.3),
                "r_base": world_template.get("rg_r_base", 3.7),
                "program_id": world_template.get("rg_program_id", 42),
                "max_depth": world_template.get("rg_max_depth", 256),
            },
            solver_chain=["rg_flow"],
        )
        rg_result = await orchestrator.run_query(client, rg_query)

    summary = orchestrator.summarize([gap_result, rg_result])

    energy_feas = compute_energy_feasibility(
        world_spec,
        astro_cfg,
        queries=[gap_query, rg_query],
    )

    witness_results: Dict[str, object] = {
        gap_query.witness_id: gap_result,
        rg_query.witness_id: rg_result,
    }

    return build_toe_scenario_scores(
        toe_candidate_id=toe_candidate_id,
        world_id=world_id,
        summary=summary,
        energy_feasibility=energy_feas,
        witness_results=witness_results,  # type: ignore[arg-type]
        corpus=corpus,
    )


async def main() -> None:
    cfg = load_simuniverse_config("configs/rex_simuniverse.yaml")
    sim_cfg = cfg.get("sim_universe", {})

    corpus = load_corpus("corpora/REx.SimUniverseCorpus.v0.2.json")

    nnsl_ep = sim_cfg.get("nnsl_endpoint", {})
    nnsl_conf = NNSLConfig(
        base_url=nnsl_ep.get("base_url", "http://nnsl-toe-lab:8080"),
        timeout_seconds=int(nnsl_ep.get("timeout_seconds", 60)),
    )

    astro_cfg_raw = sim_cfg.get("astro_constraints", {})
    astro_cfg = AstroConstraintConfig(
        universe_ops_upper_bound=float(astro_cfg_raw.get("universe_ops_upper_bound", 1e120)),
        default_diag_cost_per_dim3=float(astro_cfg_raw.get("default_diag_cost_per_dim3", 10.0)),
        default_rg_cost_per_step=float(astro_cfg_raw.get("default_rg_cost_per_step", 100.0)),
        safety_margin=float(astro_cfg_raw.get("safety_margin", 10.0)),
    )

    toe_candidates = [
        "toe_candidate_faizal_mtoe",
        "toe_candidate_muh_cuh",
    ]

    world_templates = [
        {
            "index": 0,
            "host_model": "algorithmic_host",
            "physics_modules": ["lattice_hamiltonian", "rg_flow"],
            "resolution": {
                "lattice_spacing": 0.1,
                "time_step": 0.01,
                "max_steps": 1000,
            },
            "energy_budget": {
                "max_flops": 1e30,
                "max_wallclock_seconds": 3600,
                "notes": "Toy world A",
            },
            "problem_id": 123,
            "boundary_scale": 0.05,
            "gap_system_size": 6,
            "rg_question": "phase == chaotic",
            "rg_x0": 0.2,
            "rg_y0": 0.3,
            "rg_r_base": 3.7,
            "rg_program_id": 42,
            "rg_max_depth": 256,
        },
        {
            "index": 1,
            "host_model": "algorithmic_host",
            "physics_modules": ["lattice_hamiltonian", "rg_flow"],
            "resolution": {
                "lattice_spacing": 0.1,
                "time_step": 0.01,
                "max_steps": 1000,
            },
            "energy_budget": {
                "max_flops": 1e25,
                "max_wallclock_seconds": 1800,
                "notes": "Toy world B (tighter budget)",
            },
            "problem_id": 777,
            "boundary_scale": 0.02,
            "gap_system_size": 7,
            "rg_question": "phase == fixed",
            "rg_x0": 0.6,
            "rg_y0": 0.1,
            "rg_r_base": 3.2,
            "rg_program_id": 99,
            "rg_max_depth": 512,
        },
    ]

    tasks: List[object] = []
    for toe_id in toe_candidates:
        for world_template in world_templates:
            tasks.append(
                run_single_scenario(
                    nnsl_conf=nnsl_conf,
                    astro_cfg=astro_cfg,
                    corpus=corpus,
                    toe_candidate_id=toe_id,
                    world_index=world_template["index"],
                    world_template=world_template,
                )
            )

    results: List[ToeScenarioScores] = await asyncio.gather(*tasks)  # type: ignore[arg-type]

    heatmap = build_heatmap_matrix(results)
    print_heatmap_ascii(heatmap)


if __name__ == "__main__":
    asyncio.run(main())
