from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rex.sim_universe.models import ToeQuery, WorldSpec


class HashingQuantizer:
    @staticmethod
    def encode(world: WorldSpec, query: ToeQuery) -> list[float]:
        """Hash world+query into a fixed-dim vector (placeholder)."""

        return [
            float(len(world.physics_modules)),
            float(len(query.question)),
            float(len(query.solver_chain)),
            float(len(query.resource_budget)),
        ]
@dataclass
class SemanticField:
    values: list[float]
    resolution_hint: dict[str, Any]

    @classmethod
    def from_query(
        cls, world: WorldSpec, query: ToeQuery, qvec: list[float]
    ) -> "SemanticField":
        res_hint = {
            "lattice_spacing": world.resolution.lattice_spacing,
            "time_step": world.resolution.time_step,
        }
        return cls(values=qvec, resolution_hint=res_hint)
