"""Minimal pydantic stub for offline use."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any


def _serialize(value: Any):
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class BaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def model_dump(self):
        return {k: _serialize(v) for k, v in self.__dict__.items()}

    def model_dict(self):
        return self.model_dump()

    def model_dump_json(self, **kwargs):
        return json.dumps(self.model_dump(), **kwargs)

    def json(self, **kwargs):
        return self.model_dump_json(**kwargs)

    @classmethod
    def model_validate(cls, data: dict[str, Any]):
        return cls(**data)

    @classmethod
    def model_validate_json(cls, data: str):
        return cls.model_validate(json.loads(data))

    @classmethod
    def parse_raw(cls, data: str):
        return cls.model_validate_json(data)


def Field(default: Any = None, **_: Any):
    return default


HttpUrl = str
