from __future__ import annotations

from abc import ABC, abstractmethod

from rex.sim_universe.models import ToeQuery, ToeResult, ToeResultMetrics, WorldSpec
from ..semantic import SemanticField


class BaseSolver(ABC):
    @abstractmethod
    async def solve(
        self, world: WorldSpec, query: ToeQuery, field: SemanticField
    ) -> ToeResult:  # pragma: no cover - interface
        raise NotImplementedError

    @staticmethod
    def undecidability_index_placeholder() -> float:
        return 0.0

    @staticmethod
    def metrics_placeholder() -> ToeResultMetrics:
        return ToeResultMetrics(
            time_to_partial_answer=0.0,
            complexity_growth=0.0,
            sensitivity_to_resolution=0.0,
        )
