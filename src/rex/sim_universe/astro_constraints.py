from __future__ import annotations

from typing import Dict, Iterable

from pydantic import BaseModel

from .models import ToeQuery, WorldSpec


class AstroConstraintConfig(BaseModel):
    """Configuration for astro / information-theoretic compute limits."""

    universe_ops_upper_bound: float = 1e120
    default_diag_cost_per_dim3: float = 10.0
    default_rg_cost_per_step: float = 100.0
    safety_margin: float = 10.0


def _estimate_flops_spectral_gap(query: ToeQuery, cfg: AstroConstraintConfig) -> float:
    """Estimate FLOPs for a spectral gap run with a small resolution sweep."""

    rb: Dict[str, object] = query.resource_budget or {}
    base_spins = int(rb.get("system_size", 6))
    base_spins = max(3, base_spins)

    spins_list = {max(3, base_spins - 1), base_spins, base_spins + 1}
    total_cost = 0.0

    for n in spins_list:
        dim = 2 ** n
        cost = cfg.default_diag_cost_per_dim3 * float(dim**3)
        total_cost += cost

    return total_cost


def _estimate_flops_rg_flow(query: ToeQuery, cfg: AstroConstraintConfig) -> float:
    """Estimate FLOPs for RG flow runs with a three-depth sweep."""

    rb: Dict[str, object] = query.resource_budget or {}
    max_depth = int(rb.get("max_depth", 256))
    max_depth = max(16, max_depth)

    depths = {
        max(16, max_depth // 4),
        max(16, max_depth // 2),
        max(16, max_depth),
    }

    total_steps = sum(depths)
    return cfg.default_rg_cost_per_step * float(total_steps)


def estimate_required_flops(
    world: WorldSpec, queries: Iterable[ToeQuery], cfg: AstroConstraintConfig
) -> float:
    """Aggregate FLOPs required for all planned queries in a world."""

    total_flops = 0.0
    for query in queries:
        if query.witness_id.startswith("spectral_gap"):
            total_flops += _estimate_flops_spectral_gap(query, cfg)
        elif query.witness_id.startswith("rg_flow"):
            total_flops += _estimate_flops_rg_flow(query, cfg)
        else:
            total_flops += 1e6  # conservative default for unknown witnesses

    return total_flops * cfg.safety_margin


def compute_energy_feasibility(
    world: WorldSpec,
    astro_cfg: AstroConstraintConfig,
    queries: Iterable[ToeQuery] | None = None,
) -> float:
    """
    Compare required FLOPs against host and universe budgets to score feasibility.

    If required FLOPs exceed either bound, return 0. Otherwise combine slack
    against both budgets into a score in [0, 1].
    """

    host_budget = float(world.energy_budget.max_flops)
    universe_budget = float(astro_cfg.universe_ops_upper_bound)

    if host_budget <= 0.0 or universe_budget <= 0.0:
        return 0.0

    if queries is None:
        required_flops = host_budget
    else:
        required_flops = estimate_required_flops(world, queries, astro_cfg)

    if required_flops <= 0.0:
        return 0.0

    if required_flops > host_budget or required_flops > universe_budget:
        return 0.0

    r_host = required_flops / host_budget
    r_universe = required_flops / universe_budget

    slack_host = 1.0 - r_host
    slack_universe = 1.0 - r_universe

    alpha = 0.7
    beta = 0.3
    score = max(0.0, alpha * slack_host + beta * slack_universe)

    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0

    return float(score)
