"""
This module groups pure functions that return the right-hand side of differential
equations (DEs) used throughout Machwave.

They are intentionally stateless and side-effect-free so that any numerical integrator
(RK4, RK45, implicit Euler, JAX-based solvers, etc.) can consume them without
modification.

Variable names may not be according to PEP8, since the common notation in academic
literature is preferred for readability.
"""

from .lre_mass_balance import compute_chamber_pressure_mass_balance_lre
from .point_mass_trajectory import compute_point_mass_trajectory
from .srm_mass_balance import compute_chamber_pressure_mass_balance_srm

__all__ = [
    "compute_chamber_pressure_mass_balance_srm",
    "compute_chamber_pressure_mass_balance_lre",
    "compute_point_mass_trajectory",
]
