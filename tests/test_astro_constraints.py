import pytest

from rex.sim_universe.astro_constraints import (
    AstroConstraintConfig,
    compute_energy_feasibility,
    estimate_required_flops,
)
from rex.sim_universe.models import EnergyBudgetConfig, ResolutionConfig, ToeQuery, WorldSpec


@pytest.fixture()
def toy_world():
    return WorldSpec(
        world_id="w",
        toe_candidate_id="toe",
        host_model="algorithmic_host",
        physics_modules=["lattice_hamiltonian", "rg_flow"],
        resolution=ResolutionConfig(),
        energy_budget=EnergyBudgetConfig(max_flops=1e15, max_wallclock_seconds=100.0),
    )


def test_energy_feasibility_respects_bounds(toy_world):
    cfg = AstroConstraintConfig(
        universe_ops_upper_bound=1e20,
        default_diag_cost_per_dim3=1.0,
        default_rg_cost_per_step=1.0,
        safety_margin=1.0,
    )
    q_gap = ToeQuery(
        world_id=toy_world.world_id,
        witness_id="spectral_gap_2d",
        question="gap > 0.1",
        resource_budget={"system_size": 3},
        solver_chain=["spectral_gap"],
    )
    q_rg = ToeQuery(
        world_id=toy_world.world_id,
        witness_id="rg_flow_uncomputable",
        question="phase == chaotic",
        resource_budget={"max_depth": 32},
        solver_chain=["rg_flow"],
    )

    required = estimate_required_flops(toy_world, [q_gap, q_rg], cfg)
    assert required > 0

    score = compute_energy_feasibility(toy_world, cfg, queries=[q_gap, q_rg])
    assert 0.0 < score <= 1.0


def test_energy_feasibility_returns_zero_on_overflow(toy_world):
    cfg = AstroConstraintConfig(universe_ops_upper_bound=1e10)
    q_gap = ToeQuery(
        world_id=toy_world.world_id,
        witness_id="spectral_gap_2d",
        question="gap > 0.1",
        resource_budget={"system_size": 9},
        solver_chain=["spectral_gap"],
    )

    # Force the required FLOPs to exceed host or universe limits
    score = compute_energy_feasibility(
        toy_world,
        cfg,
        queries=[q_gap],
    )
    assert score == 0.0
