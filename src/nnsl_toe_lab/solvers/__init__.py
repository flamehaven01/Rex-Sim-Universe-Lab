"""Solver package for NNSL TOE Lab."""

from .spectral_gap import solve as spectral_gap_solve
from .rg_flow import solve as rg_flow_solve

__all__ = [
    "spectral_gap_solve",
    "rg_flow_solve",
]
