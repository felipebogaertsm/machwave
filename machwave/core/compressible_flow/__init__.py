"""Compressible flow theory and analysis."""

from .nozzle import (
    apply_thrust_coefficient_correction,
    get_ideal_thrust_coefficient_components,
    get_optimal_expansion_ratio,
    get_separated_exit_conditions,
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
    get_boundary_layer_loss_fraction,
    get_kinetics_loss_fraction,
    get_nozzle_divergent_loss_fraction,
    get_two_phase_flow_loss_fraction,
)

__all__ = [
    # nozzle
    "get_optimal_expansion_ratio",
    "get_separated_exit_conditions",
    "get_ideal_thrust_coefficient_components",
    "apply_thrust_coefficient_correction",
    "get_thrust_from_thrust_coefficient",
    # isentropic
    "get_critical_pressure_ratio",
    "get_expansion_ratio_from_exit_mach",
    "get_exit_mach_from_expansion_ratio",
    "get_exit_pressure",
    "is_flow_choked",
    # losses
    "get_nozzle_divergent_loss_fraction",
    "get_kinetics_loss_fraction",
    "get_boundary_layer_loss_fraction",
    "get_two_phase_flow_loss_fraction",
]
