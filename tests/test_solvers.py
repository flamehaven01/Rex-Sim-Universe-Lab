import asyncio

import numpy as np
import pytest

from nnsl_toe_lab.semantic import SemanticField
from nnsl_toe_lab.solvers.rg_flow import solve as solve_rg
from nnsl_toe_lab.solvers.spectral_gap import solve as solve_gap
from rex.sim_universe.models import EnergyBudgetConfig, ResolutionConfig, ToeQuery, ToeResultMetrics, WorldSpec


@pytest.fixture()
def world_spec():
    return WorldSpec(
        world_id="world-test",
        toe_candidate_id="toe",
        host_model="algorithmic_host",
        physics_modules=["lattice_hamiltonian", "rg_flow"],
        resolution=ResolutionConfig(),
        energy_budget=EnergyBudgetConfig(max_flops=1e18, max_wallclock_seconds=100.0),
    )


def test_spectral_gap_solver_produces_gap(world_spec):
    query = ToeQuery(
        world_id=world_spec.world_id,
        witness_id="spectral_gap_2d",
        question="gap > 0.05",
        resource_budget={"system_size": 4, "J": 1.0, "problem_id": 11, "boundary_scale": 0.02},
        solver_chain=["spectral_gap"],
    )

    result = asyncio.run(solve_gap(world_spec, query, SemanticField([0.0], {})))

    assert result.status in {"decided_true", "decided_false"}
    assert result.approx_value is None or np.isfinite(result.approx_value)
    assert 0.0 <= result.undecidability_index <= 1.0
    assert result.metrics.time_to_partial_answer >= 0.0
    assert result.metrics.sensitivity_to_resolution >= 0.0
    assert result.t_soft_decision in {"true", "false", "unknown"}


def test_rg_flow_solver_emits_phase_and_halting(world_spec):
    query = ToeQuery(
        world_id=world_spec.world_id,
        witness_id="rg_flow_uncomputable",
        question="phase == chaotic",
        resource_budget={
            "x0": 0.25,
            "y0": 0.4,
            "r_base": 3.6,
            "program_id": 77,
            "max_depth": 64,
        },
        solver_chain=["rg_flow"],
    )

    result = asyncio.run(solve_rg(world_spec, query, SemanticField([0.0], {})))

    assert result.status in {"decided_true", "decided_false"}
    assert -1.1 <= (result.approx_value or 0.0) <= 1.1
    assert 0.0 <= result.metrics.rg_halting_indicator <= 1.0
    assert result.metrics.rg_phase_index is not None
    assert 0.0 <= result.undecidability_index <= 1.0
