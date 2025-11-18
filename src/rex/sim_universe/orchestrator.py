from __future__ import annotations

from typing import Sequence

import httpx

from .models import NNSLConfig, ToeQuery, ToeResult, WorldSpec
from .metrics import coverage_alg, coverage_meta, mean_undecidability_index


class SimUniverseOrchestrator:
    """High-level orchestrator to run SimUniverse experiments via NNSL TOE-Lab."""

    def __init__(self, nnsl_config: NNSLConfig) -> None:
        self.nnsl_config = nnsl_config

    async def create_world(self, client: httpx.AsyncClient, spec: WorldSpec) -> str:
        resp = await client.post(
            f"{self.nnsl_config.base_url}/toe/world",
            json=spec.model_dump(),
            timeout=self.nnsl_config.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["world_id"]

    async def run_query(self, client: httpx.AsyncClient, query: ToeQuery) -> ToeResult:
        resp = await client.post(
            f"{self.nnsl_config.base_url}/toe/query",
            json=query.model_dump(),
            timeout=self.nnsl_config.timeout_seconds,
        )
        resp.raise_for_status()
        return ToeResult.model_validate(resp.json())

    @staticmethod
    def summarize(results: Sequence[ToeResult]) -> dict:
        return {
            "coverage_alg": coverage_alg(results),
            "coverage_meta": coverage_meta(results),
            "mean_undecidability_index": mean_undecidability_index(results),
        }
