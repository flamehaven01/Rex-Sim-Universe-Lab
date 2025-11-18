import json
from pathlib import Path

import pytest

from rex.sim_universe.corpus import SimUniverseCorpus
from rex.sim_universe.models import ToeResult, ToeResultMetrics
from rex.sim_universe.reporting import (
    build_heatmap_matrix,
    build_toe_scenario_scores,
    compute_faizal_score,
    compute_mu_score,
    extract_rg_observables,
    format_evidence_markdown,
    print_heatmap_with_evidence_markdown,
)


def load_corpus():
    corpus_path = Path("corpora/REx.SimUniverseCorpus.v0.2.json")
    with corpus_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    return SimUniverseCorpus(**data)


def test_reporting_scores_and_evidence():
    corpus = load_corpus()

    spectral = ToeResult(
        status="decided_true",
        approx_value=0.3,
        confidence=1.0,
        undecidability_index=0.2,
        t_soft_decision="true",
        t_oracle_called=False,
        logs_ref=None,
        metrics=ToeResultMetrics(
            time_to_partial_answer=0.01,
            complexity_growth=2.0,
            sensitivity_to_resolution=0.0,
        ),
    )

    rg = ToeResult(
        status="decided_true",
        approx_value=1.0,
        confidence=0.8,
        undecidability_index=0.5,
        t_soft_decision="true",
        t_oracle_called=False,
        logs_ref=None,
        metrics=ToeResultMetrics(
            time_to_partial_answer=0.02,
            complexity_growth=1.5,
            sensitivity_to_resolution=0.1,
            rg_phase_index=1.0,
            rg_halting_indicator=0.25,
        ),
    )

    witness_results = {
        "spectral_gap_2d": spectral,
        "rg_flow_uncomputable": rg,
    }

    summary = {
        "coverage_alg": 0.8,
        "coverage_meta": 0.1,
        "mean_undecidability_index": 0.35,
    }

    scores = build_toe_scenario_scores(
        toe_candidate_id="toe_candidate_faizal_mtoe",
        world_id="world-001",
        summary=summary,
        energy_feasibility=0.5,
        witness_results=witness_results,
        corpus=corpus,
    )

    assert scores.mu_score == compute_mu_score(0.8, 0.35, 0.5)
    assert scores.faizal_score == compute_faizal_score(0.35, 0.5, 1.0, 0.25)
    assert scores.evidence, "Expected evidence links from corpus assumptions"

    phase_index, halting = extract_rg_observables(witness_results)
    assert phase_index == 1.0
    assert halting == 0.25

    matrix = build_heatmap_matrix([scores])
    assert matrix["mu_scores"][0][0] == scores.mu_score
    assert matrix["faizal_scores"][0][0] == scores.faizal_score

    evidence_md = format_evidence_markdown(scores.evidence, max_items=2)
    assert scores.evidence[0].claim_summary.split()[0] in evidence_md

    md_table = print_heatmap_with_evidence_markdown([scores])
    assert "toe_candidate_faizal_mtoe" in md_table
    assert "world-001" in md_table
