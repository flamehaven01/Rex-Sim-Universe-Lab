"""SimUniverse control plane API and Stage-5 orchestration helpers."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rex.sidrce.omega_simuniverse_integration import (
    compute_simuniverse_consistency,
    integrate_simuniverse_into_omega,
)

from .registry import (
    SimUniverseRunCreate,
    SimUniverseRunRecord,
    SimUniverseRunRegistry,
    SimUniverseRunUpdate,
)
from .stage5_loader import load_stage5_scores
from .trust_integration import build_toe_trust_summary, serialize_trust_summaries


DEFAULT_ARTIFACTS_ROOT = Path(os.environ.get("SIMUNIVERSE_ARTIFACTS", "artifacts/simuniverse_runs"))
REGISTRY_DB = os.environ.get("SIMUNIVERSE_REGISTRY_DB", "simuniverse_runs.db")


def run_stage5_for_run_id(
    *,
    env: str,
    run_id: str,
    stage5_json_path: str | Path,
    git_sha: str,
    config_path: str,
    corpus_path: str,
    registry: SimUniverseRunRegistry | None = None,
    omega_json_path: str | Path | None = None,
    artifacts_root: Path = DEFAULT_ARTIFACTS_ROOT,
    mu_min_good: float = 0.4,
    faizal_max_good: float = 0.7,
) -> Dict[str, Any]:
    """Execute the Stage-5 → trust summary → Omega merge loop for a run."""

    stage5_path = Path(stage5_json_path)
    if not stage5_path.exists():
        raise FileNotFoundError(stage5_path)

    stage5_payload = load_stage5_scores(stage5_path)
    summaries = build_toe_trust_summary(
        stage5_payload.scores,
        mu_min_good=mu_min_good,
        faizal_max_good=faizal_max_good,
        run_id=stage5_payload.run_id or run_id,
    )
    serialized = serialize_trust_summaries(summaries)

    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    trust_path = run_dir / "simuniverse_trust_summary.json"
    trust_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    sim_stats = compute_simuniverse_consistency(serialized)

    omega_report_path: Path | None = None
    omega_total: float | None = None
    if omega_json_path is not None:
        omega_report_path = run_dir / "omega_with_simuniverse.json"
        report = integrate_simuniverse_into_omega(
            omega_path=str(omega_json_path),
            simuniverse_trust_path=str(trust_path),
        )
        omega_report_path.write_text(report.json(indent=2), encoding="utf-8")
        omega_total = report.omega_total

    if registry is not None:
        registry.update_run(
            run_id,
            SimUniverseRunUpdate(
                status="success",
                omega_total=omega_total,
                simuniverse_consistency=sim_stats["value"],
            ),
        )

    return {
        "run_id": run_id,
        "env": env,
        "git_sha": git_sha,
        "config_path": config_path,
        "corpus_path": corpus_path,
        "trust_summary_path": str(trust_path),
        "omega_report_path": str(omega_report_path) if omega_report_path else None,
        "simuniverse_consistency": sim_stats["value"],
        "omega_total": omega_total,
    }


class RunRequest(BaseModel):
    env: str = Field(default="staging")
    git_sha: str
    config_path: str = Field(default="configs/rex_simuniverse.yaml")
    corpus_path: str = Field(default="corpora/REx.SimUniverseCorpus.v0.2.json")
    stage5_json_path: str = Field(default="samples/stage5_sample.json")
    omega_json_path: Optional[str] = Field(default="samples/omega_base_sample.json")


class RunResponse(BaseModel):
    run_id: str
    status: str
    trust_summary_path: Optional[str] = None
    omega_report_path: Optional[str] = None
    simuniverse_consistency: Optional[float] = None
    omega_total: Optional[float] = None


registry = SimUniverseRunRegistry(REGISTRY_DB)
app = FastAPI(title="SimUniverse Control Plane")


@app.post("/runs", response_model=RunResponse)
def create_run(req: RunRequest) -> RunResponse:
    run_id = f"{req.env}-{req.git_sha[:7]}-{uuid.uuid4().hex[:8]}"
    registry.create_run(
        SimUniverseRunCreate(
            run_id=run_id,
            env=req.env,
            git_sha=req.git_sha,
            config_path=req.config_path,
            corpus_path=req.corpus_path,
        )
    )

    try:
        result = run_stage5_for_run_id(
            env=req.env,
            run_id=run_id,
            stage5_json_path=req.stage5_json_path,
            git_sha=req.git_sha,
            config_path=req.config_path,
            corpus_path=req.corpus_path,
            registry=registry,
            omega_json_path=req.omega_json_path,
        )
    except Exception as exc:  # noqa: BLE001
        registry.update_run(
            run_id,
            SimUniverseRunUpdate(status="failed", error_message=str(exc)),
        )
        raise HTTPException(status_code=500, detail=f"SimUniverse run failed: {exc}") from exc

    return RunResponse(
        run_id=run_id,
        status="success",
        trust_summary_path=result["trust_summary_path"],
        omega_report_path=result.get("omega_report_path"),
        simuniverse_consistency=result.get("simuniverse_consistency"),
        omega_total=result.get("omega_total"),
    )


@app.get("/runs/{run_id}", response_model=SimUniverseRunRecord)
def get_run(run_id: str) -> SimUniverseRunRecord:
    record = registry.get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@app.get("/runs", response_model=List[SimUniverseRunRecord])
def list_runs(env: str | None = None, limit: int = 50) -> List[SimUniverseRunRecord]:
    return registry.list_runs(env=env, limit=limit)
