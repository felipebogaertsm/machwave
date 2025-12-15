"""Thermochemical properties of the combustion products of chemical propellants."""

from __future__ import annotations

import dataclasses
from functools import cached_property
from typing import Final

import scipy.constants

# Validation bounds (field_name: (min_value, max_value))
VALIDATION_BOUNDS: Final[dict[str, tuple[float, float]]] = {
    "gamma_chamber": (1.0, 2.0),
    "gamma_exhaust": (1.0, 2.0),
    "adiabatic_flame_temperature": (0.0, 5000.0),
    "molecular_weight_chamber": (0.001, 0.200),
    "molecular_weight_exhaust": (0.001, 0.200),
    "i_sp_frozen": (0.0, 600.0),
    "i_sp_shifting": (0.0, 600.0),
    "qsi_chamber": (0.0, 1.0),
    "qsi_exhaust": (0.0, 1.0),
}  # NOTE: field_name must match dataclass attributes


@dataclasses.dataclass(frozen=True, kw_only=True)
class ThermochemicalProperties:
    """Thermochemical properties for the combustion products of chemical rocket
    propellants.

    Immutable data structure containing theoretical properties from equilibrium
    calculations. All values are validated on construction.

    Args:
        gamma_chamber (float): Isentropic exponent in chamber (dimensionless).
        gamma_exhaust (float): Isentropic exponent at nozzle exit (dimensionless).
        adiabatic_flame_temperature (float): Adiabatic flame temperature [K].
        molecular_weight_chamber (float): Molecular weight in chamber [kg/mol].
        molecular_weight_exhaust (float): Molecular weight at exit [kg/mol].
        i_sp_frozen (float): Frozen flow specific impulse [s].
        i_sp_shifting (float): Shifting equilibrium specific impulse [s].
        qsi_chamber (float): Condensed-phase species content in chamber [mol/(100g)].
        qsi_exhaust (float): Condensed-phase species content at exit [mol/(100g)].

    Properties:
        R_chamber (float): Specific gas constant for chamber [J/(kg·K)].
        R_exhaust (float): Specific gas constant for exhaust [J/(kg·K)].
        is_two_phase_flow (bool): True if combustion produces condensed-phase species.

    Raises:
        ValueError: If any parameter is outside valid physical range.
    """

    gamma_chamber: float
    gamma_exhaust: float
    adiabatic_flame_temperature: float
    molecular_weight_chamber: float
    molecular_weight_exhaust: float
    i_sp_frozen: float
    i_sp_shifting: float
    qsi_chamber: float
    qsi_exhaust: float

    def __post_init__(self) -> None:
        """Validate all properties are within physical bounds."""
        for field_name, value in self.__dict__.items():
            if field_name in VALIDATION_BOUNDS:
                min_val, max_val = VALIDATION_BOUNDS[field_name]
                # Allow qsi to be exactly 0.0 (liquid propellants)
                if field_name in ("qsi_chamber", "qsi_exhaust"):
                    if not (min_val <= value <= max_val):
                        raise ValueError(
                            f"{field_name}={value} outside valid range "
                            f"[{min_val}, {max_val}]"
                        )
                else:
                    if not (min_val < value <= max_val):
                        raise ValueError(
                            f"{field_name}={value} outside valid range "
                            f"({min_val}, {max_val}]"
                        )

        # Cross-property validation
        if self.i_sp_shifting < self.i_sp_frozen:
            raise ValueError(
                f"i_sp_shifting ({self.i_sp_shifting}) must be >= "
                f"i_sp_frozen ({self.i_sp_frozen})"
            )

    @cached_property
    def R_chamber(self) -> float:
        """Specific gas constant for chamber.

        Returns:
            float: Specific gas constant [J/(kg·K)].
        """
        return scipy.constants.R / self.molecular_weight_chamber

    @cached_property
    def R_exhaust(self) -> float:
        """Specific gas constant for exhaust.

        Returns:
            float: Specific gas constant [J/(kg·K)].
        """
        return scipy.constants.R / self.molecular_weight_exhaust

    @property
    def is_two_phase_flow(self) -> bool:
        """Check if combustion produces condensed-phase species.

        Returns:
            bool: True if qsi_chamber > 0, False otherwise.
        """
        return self.qsi_chamber > 0.0
