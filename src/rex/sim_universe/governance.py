from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from .reporting import ToeScenarioScores


@dataclass(frozen=True)
class ToeTrustSummary:
    """Aggregate SimUniverse metrics for a TOE candidate."""

    toe_candidate_id: str
    runs: int
    mu_score_avg: float
    faizal_score_avg: float
    undecidability_avg: float
    energy_feasibility_avg: float
    low_trust_flag: bool


def build_trust_summaries(
    scores: Sequence[ToeScenarioScores],
    *,
    mu_min_good: float = 0.4,
    faizal_max_good: float = 0.7,
) -> List[ToeTrustSummary]:
    """Aggregate MUH/Faizal signals per TOE candidate."""

    bucket: Dict[str, List[ToeScenarioScores]] = {}
    for score in scores:
        bucket.setdefault(score.toe_candidate_id, []).append(score)

    summaries: List[ToeTrustSummary] = []
    for toe_id, runs in bucket.items():
        count = len(runs)
        mu_avg = sum(item.mu_score for item in runs) / count
        faizal_avg = sum(item.faizal_score for item in runs) / count
        u_avg = sum(item.mean_undecidability_index for item in runs) / count
        energy_avg = sum(item.energy_feasibility for item in runs) / count

        low_trust = mu_avg < mu_min_good and faizal_avg > faizal_max_good

        summaries.append(
            ToeTrustSummary(
                toe_candidate_id=toe_id,
                runs=count,
                mu_score_avg=mu_avg,
                faizal_score_avg=faizal_avg,
                undecidability_avg=u_avg,
                energy_feasibility_avg=energy_avg,
                low_trust_flag=low_trust,
            )
        )

    summaries.sort(key=lambda entry: entry.toe_candidate_id)
    return summaries


def serialize_trust_summaries(
    summaries: Sequence[ToeTrustSummary],
    *,
    run_id: str | None = None,
) -> List[dict]:
    """Turn trust summaries into JSON-serializable dictionaries."""

    payload: List[dict] = []
    for summary in summaries:
        item = {
            "toe_candidate_id": summary.toe_candidate_id,
            "runs": summary.runs,
            "mu_score_avg": summary.mu_score_avg,
            "faizal_score_avg": summary.faizal_score_avg,
            "undecidability_avg": summary.undecidability_avg,
            "energy_feasibility_avg": summary.energy_feasibility_avg,
            "low_trust_flag": summary.low_trust_flag,
        }
        if run_id is not None:
            item["run_id"] = run_id
        payload.append(item)
    return payload


def format_prometheus_metrics(summaries: Sequence[ToeTrustSummary]) -> str:
    """Produce Prometheus exposition text for the trust summaries."""

    lines = [
        "# HELP simuniverse_mu_score_avg Average MUH score per TOE candidate.",
        "# TYPE simuniverse_mu_score_avg gauge",
    ]
    for summary in summaries:
        lines.append(
            f'simuniverse_mu_score_avg{{toe_candidate="{summary.toe_candidate_id}"}} '
            f"{summary.mu_score_avg:.6f}"
        )

    lines.extend(
        [
            "# HELP simuniverse_faizal_score_avg Average Faizal score per TOE candidate.",
            "# TYPE simuniverse_faizal_score_avg gauge",
        ]
    )
    for summary in summaries:
        lines.append(
            f'simuniverse_faizal_score_avg{{toe_candidate="{summary.toe_candidate_id}"}} '
            f"{summary.faizal_score_avg:.6f}"
        )

    lines.extend(
        [
            "# HELP simuniverse_energy_feasibility_avg Mean energy feasibility per TOE candidate.",
            "# TYPE simuniverse_energy_feasibility_avg gauge",
        ]
    )
    for summary in summaries:
        lines.append(
            f'simuniverse_energy_feasibility_avg{{toe_candidate="{summary.toe_candidate_id}"}} '
            f"{summary.energy_feasibility_avg:.6f}"
        )

    lines.extend(
        [
            "# HELP simuniverse_undecidability_avg Mean undecidability index per TOE candidate.",
            "# TYPE simuniverse_undecidability_avg gauge",
        ]
    )
    for summary in summaries:
        lines.append(
            f'simuniverse_undecidability_avg{{toe_candidate="{summary.toe_candidate_id}"}} '
            f"{summary.undecidability_avg:.6f}"
        )

    lines.extend(
        [
            "# HELP simuniverse_low_trust_flag Whether the TOE candidate is currently flagged as low trust (1=yes,0=no).",
            "# TYPE simuniverse_low_trust_flag gauge",
        ]
    )
    for summary in summaries:
        value = 1.0 if summary.low_trust_flag else 0.0
        lines.append(
            f'simuniverse_low_trust_flag{{toe_candidate="{summary.toe_candidate_id}"}} '
            f"{value:.0f}"
        )

    return "\n".join(lines)


def simuniverse_quality(
    mu_score: float,
    faizal_score: float,
    *,
    undecidability: float | None = None,
    energy_feasibility: float | None = None,
    mu_weight: float = 0.4,
    faizal_weight: float = 0.3,
    undecidability_weight: float = 0.2,
    energy_weight: float = 0.1,
) -> float:
    """Combine MUH, Faizal, undecidability, and energy signals into one value."""

    # Clamp weights to keep the computation predictable and normalise afterwards.
    weights = [
        max(0.0, mu_weight),
        max(0.0, faizal_weight),
        max(0.0, undecidability_weight),
        max(0.0, energy_weight),
    ]
    total_weight = sum(weights) or 1.0
    w_mu, w_f, w_u, w_e = [w / total_weight for w in weights]

    q_mu = max(0.0, min(1.0, mu_score))
    q_f = 1.0 - max(0.0, min(1.0, faizal_score))
    q_u = 0.0 if undecidability is None else max(0.0, min(1.0, undecidability))
    q_e = 0.0 if energy_feasibility is None else max(0.0, min(1.0, energy_feasibility))

    quality = w_mu * q_mu + w_f * q_f + w_u * q_u + w_e * q_e
    return max(0.0, min(1.0, quality))


def adjust_route_omega(
    base_omega: float,
    sim_quality: float,
    trust_tier: str,
    *,
    tier_multipliers: Dict[str, float] | None = None,
) -> float:
    """Blend base omega with SimUniverse quality and tier penalties."""

    multipliers = tier_multipliers or {
        "high": 1.0,
        "normal": 0.9,
        "low": 0.6,
        "unknown": 0.8,
    }
    tier_factor = multipliers.get(trust_tier, multipliers["unknown"])
    omega = 0.6 * base_omega + 0.4 * sim_quality
    return omega * tier_factor


def compute_trust_tier_from_failures(
    prev_tier: str,
    failure_count: int,
    *,
    failure_threshold: int = 3,
) -> str:
    """Escalate to a low tier when repeated Stage-5 gate failures occur."""

    if failure_count >= failure_threshold:
        return "low"
    if prev_tier == "unknown":
        return "normal"
    return prev_tier
