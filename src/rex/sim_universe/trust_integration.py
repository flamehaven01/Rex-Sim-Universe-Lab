"""SimUniverse trust aggregation plus ASDP/Meta-Router integration helpers."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from .reporting import ToeScenarioScores


@dataclass
class ToeTrustSummary:
    """Aggregate metrics describing a TOE candidate across Stage-5 worlds."""

    toe_candidate_id: str
    runs: int
    mu_score_avg: float
    faizal_score_avg: float
    undecidability_avg: float
    energy_feasibility_avg: float
    low_trust_flag: bool
    run_id: str | None = None

    def to_payload(self) -> dict:
        payload = {
            "toe_candidate_id": self.toe_candidate_id,
            "runs": self.runs,
            "mu_score_avg": self.mu_score_avg,
            "faizal_score_avg": self.faizal_score_avg,
            "undecidability_avg": self.undecidability_avg,
            "energy_feasibility_avg": self.energy_feasibility_avg,
            "low_trust_flag": self.low_trust_flag,
        }
        if self.run_id is not None:
            payload["run_id"] = self.run_id
        return payload


ScoreInput = ToeScenarioScores | Mapping[str, object]


def _score_value(score: ScoreInput, field: str, default: float = 0.0) -> float:
    if isinstance(score, ToeScenarioScores):
        return float(getattr(score, field, default))
    value = score.get(field, default)
    return float(value)


def _score_toe_id(score: ScoreInput) -> str:
    if isinstance(score, ToeScenarioScores):
        return score.toe_candidate_id
    value = score.get("toe_candidate_id")
    if value is None:
        raise KeyError("toe_candidate_id is required for trust summaries")
    return str(value)


def build_toe_trust_summary(
    scores: Sequence[ScoreInput],
    mu_min_good: float = 0.4,
    faizal_max_good: float = 0.7,
    run_id: str | None = None,
) -> List[ToeTrustSummary]:
    """Aggregate ToeScenarioScores objects into ToeTrustSummary entries."""

    grouped: Dict[str, List[ScoreInput]] = defaultdict(list)
    for score in scores:
        grouped[_score_toe_id(score)].append(score)

    summaries: List[ToeTrustSummary] = []
    for toe_id, group in grouped.items():
        n = len(group)
        mu_avg = sum(_score_value(item, "mu_score") for item in group) / n
        faizal_avg = sum(_score_value(item, "faizal_score") for item in group) / n
        undecidability_avg = (
            sum(_score_value(item, "mean_undecidability_index") for item in group) / n
        )
        energy_avg = sum(_score_value(item, "energy_feasibility") for item in group) / n

        low_trust = (mu_avg < mu_min_good) and (faizal_avg > faizal_max_good)

        summaries.append(
            ToeTrustSummary(
                toe_candidate_id=toe_id,
                runs=n,
                mu_score_avg=mu_avg,
                faizal_score_avg=faizal_avg,
                undecidability_avg=undecidability_avg,
                energy_feasibility_avg=energy_avg,
                low_trust_flag=low_trust,
                run_id=run_id,
            )
        )

    return summaries


def serialize_trust_summaries(summaries: Iterable[ToeTrustSummary]) -> List[dict]:
    """Convert ToeTrustSummary objects to JSON-friendly dicts."""

    return [summary.to_payload() for summary in summaries]


def update_registry_with_trust(
    registry_doc: Mapping[str, object],
    trust_summary: Sequence[Mapping[str, object] | ToeTrustSummary],
    *,
    low_trust_tag: str = "simuniverse.low_trust",
    fallback_run_id: str | None = None,
) -> dict:
    """Patch an ASDP registry dictionary with SimUniverse trust metrics."""

    updated = deepcopy(registry_doc)
    toe_entries = updated.get("toe_candidates")
    if not isinstance(toe_entries, list):
        return updated

    normalized: Dict[str, Mapping[str, object]] = {}
    for entry in trust_summary:
        if isinstance(entry, ToeTrustSummary):
            payload = entry.to_payload()
        else:
            payload = dict(entry)
        toe_id = str(payload.get("toe_candidate_id"))
        normalized[toe_id] = payload

    for entry in toe_entries:
        toe_id = entry.get("id")
        if toe_id is None:
            continue
        payload = normalized.get(str(toe_id))
        if payload is None:
            continue

        trust_block: MutableMapping[str, object] = entry.setdefault("trust", {})
        sim_block: MutableMapping[str, object] = trust_block.setdefault("simuniverse", {})
        sim_block.update(
            mu_score_avg=payload.get("mu_score_avg", 0.0),
            faizal_score_avg=payload.get("faizal_score_avg", 0.0),
            undecidability_avg=payload.get("undecidability_avg", 0.0),
            energy_feasibility_avg=payload.get("energy_feasibility_avg", 0.0),
            low_trust_flag=payload.get("low_trust_flag", False),
        )
        sim_block["last_update_run_id"] = payload.get("run_id") or fallback_run_id

        low_trust_flag = bool(payload.get("low_trust_flag"))
        current_tier = str(trust_block.get("tier", "unknown"))
        if low_trust_flag:
            trust_block["tier"] = "low"
        elif current_tier in {"unknown", "", "low"}:
            trust_block["tier"] = "normal"

        tags = set(entry.get("sovereign_tags", []))
        if low_trust_flag:
            tags.add(low_trust_tag)
        else:
            tags.discard(low_trust_tag)
        entry["sovereign_tags"] = sorted(tags)

    return updated


def simuniverse_quality(mu_score: float, faizal_score: float) -> float:
    """Blend MUH and Faizal scores into a normalized [0, 1] quality signal."""

    quality = 0.7 * mu_score + 0.3 * (1.0 - faizal_score)
    return max(0.0, min(1.0, quality))


def route_omega(base_omega: float, sim_q: float, trust_tier: str) -> float:
    """Apply trust-tier penalties to an omega score using SimUniverse quality."""

    tier_factor = {
        "high": 1.0,
        "normal": 0.9,
        "low": 0.6,
        "unknown": 0.8,
    }.get(trust_tier, 0.8)

    omega_sim = 0.6 * base_omega + 0.4 * sim_q
    return max(0.0, min(1.0, omega_sim * tier_factor))


def compute_trust_tier_from_failures(
    prev_tier: str,
    failure_count: int,
    *,
    failure_threshold: int = 3,
) -> str:
    """Derive a trust tier using Stage-5 failure counters."""

    if failure_count >= failure_threshold:
        return "low"
    if prev_tier in {"unknown", "", "low"}:
        return "normal"
    return prev_tier
