from __future__ import annotations

from pathlib import Path

from rex.sim_universe.control_plane import run_stage5_for_run_id
from rex.sim_universe.registry import SimUniverseRunCreate, SimUniverseRunRegistry


def test_run_stage5_pipeline(tmp_path: Path) -> None:
    registry = SimUniverseRunRegistry(tmp_path / "runs.db")
    run_id = "staging-abcdef01"
    registry.create_run(
        SimUniverseRunCreate(
            run_id=run_id,
            env="staging",
            git_sha="abcdef0123456789",
            config_path="configs/rex_simuniverse.yaml",
            corpus_path="corpora/REx.SimUniverseCorpus.v0.2.json",
        )
    )

    result = run_stage5_for_run_id(
        env="staging",
        run_id=run_id,
        stage5_json_path=Path("samples/stage5_sample.json"),
        git_sha="abcdef0123456789",
        config_path="configs/rex_simuniverse.yaml",
        corpus_path="corpora/REx.SimUniverseCorpus.v0.2.json",
        registry=registry,
        omega_json_path=Path("samples/omega_base_sample.json"),
        artifacts_root=tmp_path,
    )

    run_dir = tmp_path / run_id
    assert run_dir.exists()
    assert (run_dir / "simuniverse_trust_summary.json").exists()
    assert (run_dir / "omega_with_simuniverse.json").exists()
    assert result["simuniverse_consistency"] is not None

    record = registry.get_run(run_id)
    assert record is not None
    assert record.status == "success"
    assert record.simuniverse_consistency == result["simuniverse_consistency"]
