"""Lightweight FastAPI stub for offline testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Tuple

from . import responses
from .responses import PlainTextResponse


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class _Route:
    method: str
    path: str
    handler: Callable[..., Any]


class FastAPI:
    """Minimal subset of FastAPI used for documentation and tests."""

    def __init__(self, title: str | None = None) -> None:
        self.title = title
        self._routes: List[_Route] = []

    def _register(self, method: str, path: str, handler: Callable[..., Any]) -> Callable[..., Any]:
        self._routes.append(_Route(method=method.upper(), path=path, handler=handler))
        return handler

    def get(self, path: str, response_model: object | None = None, response_class: object | None = None):  # noqa: D401
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._register("GET", path, func)

        return decorator

    def post(self, path: str, response_model: object | None = None, response_class: object | None = None):  # noqa: D401
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._register("POST", path, func)

        return decorator

    # Minimal helpers for tests to inspect routes if desired
    @property
    def routes(self) -> Tuple[_Route, ...]:
        return tuple(self._routes)


__all__ = ["FastAPI", "HTTPException", "PlainTextResponse", "responses"]
