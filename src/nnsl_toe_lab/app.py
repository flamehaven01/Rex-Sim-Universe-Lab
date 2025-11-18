from __future__ import annotations

from fastapi import FastAPI, HTTPException

from rex.sim_universe.models import ToeResult
from .models import ToeQuery, WorldSpec
from .semantic import HashingQuantizer, SemanticField
from .solvers import rg_flow, spectral_gap

app = FastAPI(title="NNSL TOE Lab", version="0.1.0")

_worlds: dict[str, WorldSpec] = {}


@app.get("/health", response_model=dict)
async def health() -> dict:
    return {"status": "ok"}


@app.post("/toe/world")
async def create_world(spec: WorldSpec) -> dict:
    world_id = spec.world_id
    if world_id in _worlds:
        raise HTTPException(status_code=409, detail="world_id already exists")
    _worlds[world_id] = spec
    return {"world_id": world_id}


@app.post("/toe/query", response_model=ToeResult)
async def run_query(query: ToeQuery) -> ToeResult:
    if query.world_id not in _worlds:
        raise HTTPException(status_code=404, detail="world not found")

    world = _worlds[query.world_id]
    qvec = HashingQuantizer.encode(world, query)
    field = SemanticField.from_query(world, query, qvec)

    if query.witness_id.startswith("spectral_gap"):
        result = await spectral_gap.solve(world, query, field)
    elif query.witness_id.startswith("rg_flow"):
        result = await rg_flow.solve(world, query, field)
    else:
        raise HTTPException(status_code=400, detail="unknown witness_id")

    return result
