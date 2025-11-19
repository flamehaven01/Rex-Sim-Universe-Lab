"""Minimal pydantic stub for offline use."""
from __future__ import annotations

from typing import Any


def _jsonable(value: Any):
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [
            _jsonable(item) for item in value
        ]
    return value


class BaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def model_dump(self):
        return {key: _jsonable(value) for key, value in self.__dict__.items()}

    def model_dict(self):
        return self.model_dump()

    @classmethod
    def model_validate(cls, data: dict[str, Any]):
        return cls(**data)


def Field(default: Any = None, **_: Any):
    return default


HttpUrl = str
