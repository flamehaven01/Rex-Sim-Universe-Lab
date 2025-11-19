from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence

from .corpus import AssumptionRole, SimUniverseCorpus
from .models import ToeResult


@dataclass
class ToeScenarioScores:
    toe_candidate_id: str
    world_id: str
    mu_score: float
    faizal_score: float
    coverage_alg: float = 0.0
    mean_undecidability_index: float = 0.0
    energy_feasibility: float = 0.0
    rg_phase_index: float = 0.0
    rg_halting_indicator: float = 0.0
    evidence: List["EvidenceLink"] = field(default_factory=list)


@dataclass
class EvidenceLink:
    claim_id: str
    paper_id: str
    role: str
    weight: float
    claim_summary: str
    paper_title: str
    section_label: str | None
    location_hint: str | None


def extract_rg_observables(results: Mapping[str, ToeResult]) -> tuple[float, float]:
    """
    Extract RG phase index and halting indicator from a dictionary of witness results.

    Expects the RG witness id key to start with ``rg_flow``.
    Returns ``(phase_index, halting_indicator)``. If missing, both are 0.0.
    """

    for wid, result in results.items():
        if wid.startswith("rg_flow"):
            phase_index = result.metrics.rg_phase_index or 0.0
            halting_indicator = result.metrics.rg_halting_indicator or 0.0
            return float(phase_index), float(halting_indicator)
    return 0.0, 0.0


def compute_mu_score(
    coverage_alg: float,
    mean_undecidability_index: float,
    energy_feasibility: float,
) -> float:
    """
    MUH-like score: high when the model is algorithmically coverable,
    low undecidability, and energy-feasible.
    """

    mu = coverage_alg * energy_feasibility * max(0.0, 1.0 - mean_undecidability_index)
    return float(mu)


def compute_faizal_score(
    mean_undecidability_index: float,
    energy_feasibility: float,
    rg_phase_index: float,
    rg_halting_indicator: float,
) -> float:
    """
    Faizal-like score: high when undecidability is high, energy feasibility is low,
    and RG dynamics are chaotic and non-halting.

    The ``chaos_bonus`` term amplifies cases with:
      - chaotic phase (phase_index ~ +1),
      - low halting indicator (unstable phase across resolutions).
    """

    chaos_bonus = max(0.0, rg_phase_index) * max(0.0, 1.0 - rg_halting_indicator)
    faizal = mean_undecidability_index * max(0.0, 1.0 - energy_feasibility) * (
        1.0 + chaos_bonus
    )
    return float(faizal)


def build_toe_scenario_scores(
    toe_candidate_id: str,
    world_id: str,
    summary: Mapping[str, float],
    energy_feasibility: float,
    witness_results: Mapping[str, ToeResult],
    corpus: SimUniverseCorpus,
) -> ToeScenarioScores:
    """
    Build Faizal/MUH scores for a single (toe_candidate, world) scenario and attach
    structured evidence derived from the corpus assumptions.
    """

    coverage_alg = float(summary.get("coverage_alg", 0.0))
    mean_u = float(summary.get("mean_undecidability_index", 0.0))

    phase_idx, halting = extract_rg_observables(witness_results)

    mu_score = compute_mu_score(
        coverage_alg=coverage_alg,
        mean_undecidability_index=mean_u,
        energy_feasibility=energy_feasibility,
    )
    faizal_score = compute_faizal_score(
        mean_undecidability_index=mean_u,
        energy_feasibility=energy_feasibility,
        rg_phase_index=phase_idx,
        rg_halting_indicator=halting,
    )

    evidence_links = collect_evidence_links(corpus, toe_candidate_id=toe_candidate_id)

    return ToeScenarioScores(
        toe_candidate_id=toe_candidate_id,
        world_id=world_id,
        mu_score=mu_score,
        faizal_score=faizal_score,
        coverage_alg=coverage_alg,
        mean_undecidability_index=mean_u,
        energy_feasibility=energy_feasibility,
        rg_phase_index=phase_idx,
        rg_halting_indicator=halting,
        evidence=evidence_links,
    )


def build_heatmap_matrix(scores: Sequence[ToeScenarioScores]) -> Dict[str, object]:
    """
    Build a simple "heatmap" data structure for Faizal vs MUH scores.
    """

    toe_ids = sorted({score.toe_candidate_id for score in scores})
    world_ids = sorted({score.world_id for score in scores})

    idx_toe = {toe_id: i for i, toe_id in enumerate(toe_ids)}
    idx_world = {world_id: j for j, world_id in enumerate(world_ids)}

    mu_scores: List[List[float]] = [[0.0 for _ in world_ids] for _ in toe_ids]
    faizal_scores: List[List[float]] = [[0.0 for _ in world_ids] for _ in toe_ids]

    for score in scores:
        i = idx_toe[score.toe_candidate_id]
        j = idx_world[score.world_id]
        mu_scores[i][j] = score.mu_score
        faizal_scores[i][j] = score.faizal_score

    return {
        "toe_candidates": toe_ids,
        "world_ids": world_ids,
        "mu_scores": mu_scores,
        "faizal_scores": faizal_scores,
    }


def print_heatmap_ascii(matrix: Dict[str, object]) -> None:
    """
    Print a crude ASCII representation of the Faizal/MUH heatmap for quick inspection.
    """

    toe_ids: List[str] = matrix["toe_candidates"]  # type: ignore[assignment]
    world_ids: List[str] = matrix["world_ids"]  # type: ignore[assignment]
    mu_matrix: List[List[float]] = matrix["mu_scores"]  # type: ignore[assignment]
    faizal_matrix: List[List[float]] = matrix["faizal_scores"]  # type: ignore[assignment]

    print("=== MUH score heatmap ===")
    header = "toe/world".ljust(20) + "".join(world.ljust(16) for world in world_ids)
    print(header)
    for toe_id, row in zip(toe_ids, mu_matrix):
        line = toe_id.ljust(20) + "".join(f"{value:0.3f}".ljust(16) for value in row)
        print(line)

    print("\n=== Faizal score heatmap ===")
    header = "toe/world".ljust(20) + "".join(world.ljust(16) for world in world_ids)
    print(header)
    for toe_id, row in zip(toe_ids, faizal_matrix):
        line = toe_id.ljust(20) + "".join(f"{value:0.3f}".ljust(16) for value in row)
        print(line)


def collect_evidence_links(
    corpus: SimUniverseCorpus,
    toe_candidate_id: str,
    max_items: int = 5,
) -> List[EvidenceLink]:
    """
    Collect a small list of evidence links for the given TOE candidate based on
    the corpus assumptions.
    """

    toe_index = corpus.toe_index()
    claim_index = corpus.claim_index()
    paper_index = corpus.paper_index()

    toe = toe_index.get(toe_candidate_id)
    if toe is None:
        return []

    role_priority = {
        AssumptionRole.SUPPORT: 0,
        AssumptionRole.CONTEST: 1,
        AssumptionRole.CONTEXT: 2,
    }

    sorted_assumptions = sorted(
        toe.assumptions,
        key=lambda assumption: (role_priority.get(assumption.role, 3), -assumption.weight),
    )

    links: List[EvidenceLink] = []
    for assumption in sorted_assumptions:
        claim = claim_index.get(assumption.claim_id)
        if claim is None:
            continue
        paper = paper_index.get(claim.paper_id)
        if paper is None:
            continue

        links.append(
            EvidenceLink(
                claim_id=claim.id,
                paper_id=claim.paper_id,
                role=assumption.role.value,
                weight=assumption.weight,
                claim_summary=claim.summary,
                paper_title=paper.title,
                section_label=claim.section_label,
                location_hint=claim.location_hint,
            )
        )

        if len(links) >= max_items:
            break

    return links


def format_evidence_markdown(evidence: List[EvidenceLink], max_items: int = 3) -> str:
    """
    Format a compact Markdown snippet that lists the strongest evidence items.
    """

    items = evidence[:max_items]
    lines: List[str] = []
    for entry in items:
        location = entry.section_label or entry.location_hint or ""
        location_suffix = f", {location}" if location else ""
        lines.append(
            f"- [{entry.role}, {entry.weight:0.2f}] {entry.paper_title}{location_suffix}: {entry.claim_summary}"
        )
    return "\n".join(lines)


def print_heatmap_with_evidence_markdown(scores: Sequence[ToeScenarioScores]) -> str:
    """
    Build a Markdown table that pairs MUH/Faizal scores with evidence snippets
    for each TOE candidate and world combination.
    """

    toe_ids = sorted({score.toe_candidate_id for score in scores})
    world_ids = sorted({score.world_id for score in scores})

    lookup: Dict[tuple[str, str], ToeScenarioScores] = {
        (score.toe_candidate_id, score.world_id): score for score in scores
    }

    lines: List[str] = []
    lines.append("## TOE vs World – Evidence-aware Heatmap\n")
    lines.append("| TOE candidate | World | MUH score | Faizal score | Key evidence |")
    lines.append("|---------------|-------|-----------|--------------|--------------|")

    for toe_id in toe_ids:
        for world_id in world_ids:
            scenario = lookup.get((toe_id, world_id))
            if scenario is None:
                continue
            evidence_md = format_evidence_markdown(scenario.evidence, max_items=3).replace("\n", "<br>")
            row = (
                f"| `{toe_id}` | `{world_id}` | "
                f"{scenario.mu_score:0.3f} | {scenario.faizal_score:0.3f} | {evidence_md} |"
            )
            lines.append(row)

    return "\n".join(lines)
