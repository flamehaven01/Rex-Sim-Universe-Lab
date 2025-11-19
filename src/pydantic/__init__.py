"""Minimal pydantic stub for offline use."""
from __future__ import annotations

from typing import Any


class BaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def model_dump(self):
        return self.__dict__.copy()

    def model_dict(self):
        return self.model_dump()

    @classmethod
    def model_validate(cls, data: dict[str, Any]):
        return cls(**data)


def Field(default: Any = None, **_: Any):
    return default


HttpUrl = str
