from __future__ import annotations

from pathlib import Path

from rex.sim_universe.renderers import build_react_payload, export_react_payload, serialize_scores
from rex.sim_universe.reporting import EvidenceLink, ToeScenarioScores


def _sample_scores() -> list[ToeScenarioScores]:
    return [
        ToeScenarioScores(
            toe_candidate_id="toe_candidate_demo",
            world_id="world-demo-000",
            mu_score=0.25,
            faizal_score=0.75,
            coverage_alg=0.5,
            mean_undecidability_index=0.6,
            energy_feasibility=0.4,
            rg_phase_index=1.0,
            rg_halting_indicator=0.2,
            evidence=[
                EvidenceLink(
                    claim_id="claim.demo",
                    paper_id="paper.demo",
                    role="support",
                    weight=0.9,
                    claim_summary="Toy claim summary",
                    paper_title="Demo paper",
                    section_label="Sec. 1",
                    location_hint="pp. 1-2",
                )
            ],
        )
    ]


def test_serialize_scores_returns_plain_dicts():
    serialized = serialize_scores(_sample_scores())

    assert serialized[0]["toe_candidate_id"] == "toe_candidate_demo"
    assert serialized[0]["evidence"][0]["claim_id"] == "claim.demo"


def test_build_react_payload_shapes_data():
    payload = build_react_payload(_sample_scores())

    assert payload["toe_candidates"] == ["toe_candidate_demo"]
    assert payload["world_ids"] == ["world-demo-000"]
    key = "toe_candidate_demo::world-demo-000"
    assert key in payload["scenarios"]
    assert payload["scenarios"][key]["mu_score"] == 0.25


def test_export_react_payload(tmp_path: Path):
    destination = tmp_path / "payload.json"
    export_react_payload(_sample_scores(), destination)

    contents = destination.read_text(encoding="utf-8")
    assert "toe_candidate_demo" in contents
