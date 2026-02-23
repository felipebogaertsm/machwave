"""
Compressible flow theory and analysis.
"""

from .nozzle import (
    apply_thrust_coefficient_correction,
    get_ideal_thrust_coefficient,
    get_optimal_expansion_ratio,
    get_thrust_from_thrust_coefficient,
)
from .isentropic import (
    get_critical_pressure_ratio,
    get_exit_mach_from_expansion_ratio,
    get_exit_pressure,
    get_expansion_ratio_from_exit_mach,
    is_flow_choked,
)
from .losses import (
    get_boundary_layer_percentage_loss,
    get_kinetics_percentage_loss,
    get_nozzle_divergent_percentage_loss,
    get_overall_nozzle_efficiency,
    get_two_phase_flow_percentage_loss,
)

__all__ = [
    # nozzle
    "get_optimal_expansion_ratio",
    "get_ideal_thrust_coefficient",
    "apply_thrust_coefficient_correction",
    "get_thrust_from_thrust_coefficient",
    # isentropic
    "get_critical_pressure_ratio",
    "get_expansion_ratio_from_exit_mach",
    "get_exit_mach_from_expansion_ratio",
    "get_exit_pressure",
    "is_flow_choked",
    # losses
    "get_nozzle_divergent_percentage_loss",
    "get_kinetics_percentage_loss",
    "get_boundary_layer_percentage_loss",
    "get_two_phase_flow_percentage_loss",
    "get_overall_nozzle_efficiency",
]
