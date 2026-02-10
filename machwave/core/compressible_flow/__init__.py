"""
Compressible flow theory and analysis.
"""

from .delaval_nozzle import (
    apply_thrust_coefficient_correction,
    get_ideal_thrust_coefficient,
    get_optimal_expansion_ratio,
)
from .isentropic import (
    get_critical_pressure_ratio,
    get_exit_mach,
    get_exit_pressure,
    get_expansion_ratio_from_mach,
    is_flow_choked,
)
from .losses import (
    get_boundary_layer_percentage_loss,
    get_kinetics_percentage_loss,
    get_nozzle_divergent_percentage_loss,
    get_overall_nozzle_efficiency,
    get_two_phase_flow_percentage_loss,
)
from .thrust import (
    get_thrust_coefficient_from_thrust,
    get_thrust_from_thrust_coefficient,
)

__all__ = [
    # delaval_nozzle
    "get_optimal_expansion_ratio",
    "get_ideal_thrust_coefficient",
    "apply_thrust_coefficient_correction",
    # isentropic
    "get_critical_pressure_ratio",
    "get_expansion_ratio_from_mach",
    "get_exit_mach",
    "get_exit_pressure",
    "is_flow_choked",
    # losses
    "get_nozzle_divergent_percentage_loss",
    "get_kinetics_percentage_loss",
    "get_boundary_layer_percentage_loss",
    "get_two_phase_flow_percentage_loss",
    "get_overall_nozzle_efficiency",
    # thrust
    "get_thrust_from_thrust_coefficient",
    "get_thrust_coefficient_from_thrust",
]
