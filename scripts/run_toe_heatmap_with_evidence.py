from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - optional dependency for offline tests
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from rex.sim_universe.astro_constraints import AstroConstraintConfig, compute_energy_feasibility
from rex.sim_universe.corpus import SimUniverseCorpus
from rex.sim_universe.models import (
    EnergyBudgetConfig,
    NNSLConfig,
    ResolutionConfig,
    ToeQuery,
    WorldSpec,
)
from rex.sim_universe.reporting import (
    ToeScenarioScores,
    build_toe_scenario_scores,
    print_heatmap_with_evidence_markdown,
)
from rex.sim_universe.renderers import (
    export_react_payload,
    render_html_report,
    write_notebook_report,
)

try:  # pragma: no cover - optional dependency for offline tests
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]


def load_yaml(path: str) -> dict:
    if yaml is None:  # pragma: no cover - exercised when running CLI for real
        raise RuntimeError(
            "PyYAML is required to load SimUniverse configuration files; please install it first."
        )
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
    from rex.sim_universe.orchestrator import SimUniverseOrchestrator

    orchestrator = SimUniverseOrchestrator(nnsl_conf)

    world_id = f"world-{toe_candidate_id}-{world_index:03d}"
    world_spec = WorldSpec(
        world_id=world_id,
        toe_candidate_id=toe_candidate_id,
        host_model=world_template.get("host_model", "algorithmic_host"),
        physics_modules=world_template.get("physics_modules", ["lattice_hamiltonian", "rg_flow"]),
        resolution=ResolutionConfig(
            lattice_spacing=world_template["resolution"]["lattice_spacing"],
            time_step=world_template["resolution"]["time_step"],
            max_steps=world_template["resolution"]["max_steps"],
        ),
        energy_budget=EnergyBudgetConfig(
            max_flops=world_template["energy_budget"]["max_flops"],
            max_wallclock_seconds=world_template["energy_budget"]["max_wallclock_seconds"],
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
    energy_feasibility = compute_energy_feasibility(
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
        energy_feasibility=energy_feasibility,
        witness_results=witness_results,  # type: ignore[arg-type]
        corpus=corpus,
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run SimUniverse experiments and render an evidence-aware heatmap."
    )
    parser.add_argument(
        "--config",
        default="configs/rex_simuniverse.yaml",
        help="Path to the SimUniverse configuration YAML file.",
    )
    parser.add_argument(
        "--corpus",
        default="corpora/REx.SimUniverseCorpus.v0.2.json",
        help="Path to the evidence-aware SimUniverse corpus JSON file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path for saving the Markdown heatmap (prints to stdout otherwise).",
    )
    parser.add_argument(
        "--html",
        dest="html_output",
        default=None,
        help="Optional path for rendering the interactive HTML report.",
    )
    parser.add_argument(
        "--notebook",
        dest="notebook_output",
        default=None,
        help="Optional path for saving a Jupyter notebook with the same evidence.",
    )
    parser.add_argument(
        "--react-json",
        dest="react_output",
        default=None,
        help="Optional path for exporting a JSON payload suitable for the React dashboard.",
    )
    parser.add_argument(
        "--templates-dir",
        default="templates",
        help="Directory that stores Jinja2 templates for the HTML report.",
    )
    return parser


def emit_markdown(markdown: str, output_path: str | None) -> Path | None:
    """Print or persist the Markdown table depending on ``output_path``."""

    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(markdown, encoding="utf-8")
        print(f"Evidence-aware heatmap saved to {destination}")
        return destination

    print(markdown)
    return None


async def run_cli(
    config_path: str,
    corpus_path: str,
    markdown_path: str | None,
    *,
    html_path: str | None,
    notebook_path: str | None,
    react_path: str | None,
    templates_dir: str,
) -> None:
    if httpx is None:  # pragma: no cover - exercised during real CLI runs
        raise RuntimeError(
            "httpx is required to contact the NNSL TOE-Lab service; please install it first."
        )

    cfg = load_yaml(config_path)
    sim_cfg = cfg.get("sim_universe", {})

    corpus = load_corpus(corpus_path)

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
        "toe_candidate_watson_rg",
        "toe_candidate_cubitt_gap",
    ]

    world_templates = [
        {
            "index": 0,
            "host_model": "algorithmic_host",
            "physics_modules": ["lattice_hamiltonian", "rg_flow"],
            "resolution": {"lattice_spacing": 0.1, "time_step": 0.01, "max_steps": 1000},
            "energy_budget": {
                "max_flops": 1e30,
                "max_wallclock_seconds": 3600,
                "notes": "World A",
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
        }
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

    markdown = print_heatmap_with_evidence_markdown(results)
    emit_markdown(markdown, markdown_path)

    if html_path:
        destination = render_html_report(results, template_dir=templates_dir, output_path=html_path)
        print(f"HTML report saved to {destination}")

    if notebook_path:
        destination = write_notebook_report(results, output_path=notebook_path)
        print(f"Notebook saved to {destination}")

    if react_path:
        destination = export_react_payload(results, react_path)
        print(f"React payload saved to {destination}")


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    asyncio.run(
        run_cli(
            args.config,
            args.corpus,
            args.output,
            html_path=args.html_output,
            notebook_path=args.notebook_output,
            react_path=args.react_output,
            templates_dir=args.templates_dir,
        )
    )


if __name__ == "__main__":
    main()
