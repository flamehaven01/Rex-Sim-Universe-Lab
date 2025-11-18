"""Lightweight numpy stub for offline testing."""
from __future__ import annotations

import math
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


linalg = _Linalg()


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
