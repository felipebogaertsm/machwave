"""Compressible flow theory and analysis."""

from .nozzle import (
    get_effective_nozzle_throat_area,
    get_ideal_thrust_coefficient_terms,
    get_optimal_expansion_ratio,
    get_separated_exit_conditions,
    get_thrust_from_thrust_coefficient,
)
from .isentropic import (
    FlowBranch,
    get_critical_pressure_ratio,
    get_exit_mach_from_expansion_ratio,
    get_exit_pressure,
    get_expansion_ratio_from_exit_mach,
    get_maximum_expansion_ratio,
    is_flow_choked,
)

__all__ = [
    # nozzle
    "get_optimal_expansion_ratio",
    "get_separated_exit_conditions",
    "get_ideal_thrust_coefficient_terms",
    "get_effective_nozzle_throat_area",
    "get_thrust_from_thrust_coefficient",
    # isentropic
    "FlowBranch",
    "get_critical_pressure_ratio",
    "get_expansion_ratio_from_exit_mach",
    "get_exit_mach_from_expansion_ratio",
    "get_exit_pressure",
    "get_maximum_expansion_ratio",
    "is_flow_choked",
]
