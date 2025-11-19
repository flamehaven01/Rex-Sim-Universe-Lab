from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence
from textwrap import dedent

from .reporting import ToeScenarioScores, build_heatmap_matrix


def _score_to_dict(score: ToeScenarioScores) -> dict:
    return {
        "toe_candidate_id": score.toe_candidate_id,
        "world_id": score.world_id,
        "mu_score": score.mu_score,
        "faizal_score": score.faizal_score,
        "coverage_alg": score.coverage_alg,
        "mean_undecidability_index": score.mean_undecidability_index,
        "energy_feasibility": score.energy_feasibility,
        "rg_phase_index": score.rg_phase_index,
        "rg_halting_indicator": score.rg_halting_indicator,
        "evidence": [
            {
                "claim_id": evidence.claim_id,
                "paper_id": evidence.paper_id,
                "role": evidence.role,
                "weight": evidence.weight,
                "claim_summary": evidence.claim_summary,
                "paper_title": evidence.paper_title,
                "section_label": evidence.section_label,
                "location_hint": evidence.location_hint,
            }
            for evidence in score.evidence
        ],
    }


def serialize_scores(scores: Sequence[ToeScenarioScores]) -> List[dict]:
    """Convert ``ToeScenarioScores`` objects into plain dictionaries."""

    return [_score_to_dict(score) for score in scores]


def build_react_payload(scores: Sequence[ToeScenarioScores]) -> dict:
    """Return a JSON-ready object for the React dashboard component."""

    heatmap = build_heatmap_matrix(scores)
    payload = dict(heatmap)
    payload["scenarios"] = {f"{s.toe_candidate_id}::{s.world_id}": _score_to_dict(s) for s in scores}
    return payload


def export_react_payload(scores: Sequence[ToeScenarioScores], output_path: str) -> Path:
    """Persist the React payload as prettified JSON."""

    payload = build_react_payload(scores)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def render_html_report(
    scores: Sequence[ToeScenarioScores],
    *,
    template_dir: str = "templates",
    template_name: str = "simuniverse_report.html",
    output_path: str = "simuniverse_report.html",
) -> Path:
    """Render the Jinja2 report for the evidence-aware heatmap."""

    try:  # pragma: no cover - exercised during CLI usage
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Jinja2 is required to render the SimUniverse HTML report; install it via `pip install jinja2`."
        ) from exc

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)

    heatmap = build_heatmap_matrix(scores)
    scenario_map: Dict[str, Dict[str, ToeScenarioScores]] = {}
    for score in scores:
        scenario_map.setdefault(score.toe_candidate_id, {})[score.world_id] = score

    scenario_json = {
        f"{score.toe_candidate_id}::{score.world_id}": _score_to_dict(score)
        for score in scores
    }

    html = template.render(
        toe_candidates=heatmap["toe_candidates"],
        world_ids=heatmap["world_ids"],
        mu_scores=heatmap["mu_scores"],
        faizal_scores=heatmap["faizal_scores"],
        scenario_map=scenario_map,
        scenario_json=json.dumps(scenario_json),
    )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
    return destination


def write_notebook_report(scores: Sequence[ToeScenarioScores], output_path: str = "SimUniverse_Results.ipynb") -> Path:
    """Generate a notebook summarising MUH vs Faizal scores and evidence links."""

    try:  # pragma: no cover - exercised during CLI usage
        import nbformat as nbf
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "nbformat is required to build the SimUniverse notebook; install it via `pip install nbformat`."
        ) from exc

    serialized = serialize_scores(scores)

    nb = nbf.v4.new_notebook()
    nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3"}

    intro = nbf.v4.new_markdown_cell(
        "# REx SimUniverse Evidence-Aware Report\n\n"
        "This notebook captures MUH vs Faizal scores for SimUniverse experiments "
        "and attaches textual evidence pulled from Faizal / Watson / Cubitt / Tegmark papers."
    )

    data_cell = nbf.v4.new_code_cell(
        "from dataclasses import asdict\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n\n"
        "scores = %s\n\n"
        "df = pd.DataFrame(scores)\n"
        "df"
        % json.dumps(serialized)
    )

    heatmap_mu = nbf.v4.new_code_cell(
        "pivot_mu = df.pivot(index='toe_candidate_id', columns='world_id', values='mu_score')\n"
        "plt.figure(figsize=(6, 4))\n"
        "plt.imshow(pivot_mu.values, aspect='auto')\n"
        "plt.xticks(range(len(pivot_mu.columns)), pivot_mu.columns, rotation=45, ha='right')\n"
        "plt.yticks(range(len(pivot_mu.index)), pivot_mu.index)\n"
        "plt.title('MUH score heatmap')\n"
        "plt.colorbar(label='MUH score')\n"
        "plt.tight_layout()\n"
        "plt.show()"
    )

    heatmap_faizal = nbf.v4.new_code_cell(
        "pivot_faizal = df.pivot(index='toe_candidate_id', columns='world_id', values='faizal_score')\n"
        "plt.figure(figsize=(6, 4))\n"
        "plt.imshow(pivot_faizal.values, aspect='auto')\n"
        "plt.xticks(range(len(pivot_faizal.columns)), pivot_faizal.columns, rotation=45, ha='right')\n"
        "plt.yticks(range(len(pivot_faizal.index)), pivot_faizal.index)\n"
        "plt.title('Faizal score heatmap')\n"
        "plt.colorbar(label='Faizal score')\n"
        "plt.tight_layout()\n"
        "plt.show()"
    )

    evidence_cell = nbf.v4.new_code_cell(
        dedent(
            """\
            for toe, group in df.groupby('toe_candidate_id'):
                print('=' * 80)
                print(f'TOE candidate: {toe}')
                for _, row in group.iterrows():
                    print('-' * 40)
                    print(f"World: {row['world_id']}")
                    print(f"MUH score: {row['mu_score']:.3f}, Faizal score: {row['faizal_score']:.3f}")
                    for ev in row['evidence']:
                        loc = ev.get('section_label') or ev.get('location_hint') or ''
                        loc_str = f', {loc}' if loc else ''
                        print(f"  - [{ev['role']}, w={ev['weight']:.2f}] {ev['paper_title']}{loc_str}: {ev['claim_summary']}")
            """
        )
    )

    nb["cells"] = [intro, data_cell, heatmap_mu, heatmap_faizal, evidence_cell]

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(nbf.writes(nb), encoding="utf-8")
    return destination
