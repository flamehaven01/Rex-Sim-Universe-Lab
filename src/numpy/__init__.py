"""Lightweight numpy stub for offline testing.

This module implements only the small subset of NumPy APIs required by the
SimUniverse toy stack and the meta/DFI helpers. It prioritizes availability
over numerical fidelity and should **not** be used for scientific workloads.
"""
from __future__ import annotations

import math
import random as _stdlib_random
from typing import Iterable, Sequence

float64 = float
complex128 = complex
bool_ = bool
pi = math.pi


class SimpleArray(list):
    def __init__(self, seq: Iterable, dtype=float):
        super().__init__(dtype(x) for x in seq)

    def copy(self):
        return SimpleArray(self, float)


def array(seq, dtype=float):
    if isinstance(seq, (list, tuple)) and seq and isinstance(seq[0], (list, tuple)):
        return [[dtype(x) for x in row] for row in seq]
    return SimpleArray(seq, dtype)


def eye(n: int, dtype=float):
    return [[dtype(1.0) if i == j else dtype(0.0) for j in range(n)] for i in range(n)]


def zeros(shape, dtype=float):
    if isinstance(shape, tuple) and len(shape) == 2:
        rows, cols = shape
        return [[dtype(0.0) for _ in range(cols)] for _ in range(rows)]
    return [dtype(0.0) for _ in range(int(shape))]


def kron(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]):
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    result = [[0.0 for _ in range(cols_a * cols_b)] for _ in range(rows_a * rows_b)]
    for i in range(rows_a):
        for j in range(cols_a):
            for k in range(rows_b):
                for l in range(cols_b):
                    result[i * rows_b + k][j * cols_b + l] = a[i][j] * b[k][l]
    return result


class _Linalg:
    @staticmethod
    def eigvalsh(matrix: Sequence[Sequence[float]]):
        size = len(matrix)
        return [float(i) for i in range(size)]

    @staticmethod
    def norm(vec: Sequence[float]) -> float:
        return math.sqrt(sum(x * x for x in vec))


class _Random:
    @staticmethod
    def randn(*shape: int):
        total = 1
        for dim in shape or (1,):
            total *= dim
        values = [_stdlib_random.gauss(0.0, 1.0) for _ in range(total)]
        if not shape or shape == (1,):
            return values[0]
        # Only minimal support for 1D outputs is required by the codebase.
        return SimpleArray(values, float)

    @staticmethod
    def random(size: int | None = None):
        if size is None:
            return _stdlib_random.random()
        return SimpleArray([_stdlib_random.random() for _ in range(size)], float)


linalg = _Linalg()
random = _Random()


def sort(values: Sequence[float]):
    return sorted(values)


def isfinite(value: float) -> bool:
    return math.isfinite(value)


def log2(value: float) -> float:
    return math.log2(value)


def sin(x: float) -> float:
    return math.sin(x)


def tanh(x: float) -> float:
    return math.tanh(x)


def isscalar(value):
    return isinstance(value, (int, float, complex))


def abs(x):
    if isinstance(x, (list, tuple, SimpleArray)):
        return SimpleArray([abs(v) for v in x], float)
    return math.fabs(x)


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def mean(values: Sequence[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def std(values: Sequence[float]) -> float:
    vals = list(values)
    if not vals:
        return 0.0
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


def pad(arr: Sequence[float], pad_width: Sequence[int], mode: str = "constant"):
    if len(pad_width) != 2:
        raise ValueError("Only 1D padding is supported in the stub.")
    left, right = pad_width
    return [0.0] * left + list(arr) + [0.0] * right


def polyfit(x: Sequence[float], y: Sequence[float], deg: int):
    # Minimal linear fit for deg == 1; higher degrees fallback to zeros.
    if deg != 1 or not x or not y or len(x) != len(y):
        return [0.0 for _ in range(deg + 1)]
    n = len(x)
    avg_x = mean(x)
    avg_y = mean(y)
    num = sum((xi - avg_x) * (yi - avg_y) for xi, yi in zip(x, y))
    den = sum((xi - avg_x) ** 2 for xi in x) or 1e-9
    slope = num / den
    intercept = avg_y - slope * avg_x
    return [slope, intercept]
