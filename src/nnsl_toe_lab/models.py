from __future__ import annotations

from pydantic import BaseModel

from rex.sim_universe.models import (
    ToeQuery as BaseToeQuery,
    ToeResult as BaseToeResult,
    WorldSpec as BaseWorldSpec,
)


class WorldSpec(BaseWorldSpec):
    """Inherit REx WorldSpec for FastAPI validation."""


class ToeQuery(BaseToeQuery):
    """Inherit REx ToeQuery for FastAPI validation."""


class ToeResult(BaseToeResult):
    """Inherit REx ToeResult for FastAPI responses."""


class Health(BaseModel):
    status: str = "ok"
