from __future__ import annotations

from pathlib import Path

from rex.sim_universe.registry import (
    SimUniverseRunCreate,
    SimUniverseRunRegistry,
    SimUniverseRunUpdate,
)


def test_registry_create_and_update(tmp_path: Path) -> None:
    db_path = tmp_path / "registry.db"
    registry = SimUniverseRunRegistry(db_path)

    create = SimUniverseRunCreate(
        run_id="staging-123",
        env="staging",
        git_sha="abc1234",
        config_path="configs/sample.yaml",
        corpus_path="corpora/sample.json",
    )
    record = registry.create_run(create)
    assert record.run_id == "staging-123"
    assert record.status == "running"

    updated = registry.update_run(
        "staging-123",
        SimUniverseRunUpdate(status="success", omega_total=0.9, simuniverse_consistency=0.8),
    )
    assert updated is not None
    assert updated.status == "success"
    assert updated.omega_total == 0.9
    assert updated.simuniverse_consistency == 0.8

    # list API should include our single run
    runs = registry.list_runs(env="staging")
    assert len(runs) == 1
    assert runs[0].run_id == "staging-123"
