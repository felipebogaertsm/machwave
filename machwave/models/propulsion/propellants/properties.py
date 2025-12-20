"""Thermochemical properties of the combustion products of chemical propellants."""

import dataclasses
import functools

import scipy.constants

# Validation bounds (field_name: (min_value, max_value))
# NOTE 1: field_name must match the dataclass' ThermochemicalProperties attributes
# NOTE 2: bounds are inclusive on both ends
VALIDATION_BOUNDS: dict[str, tuple[float, float]] = {
    "gamma_chamber": (1.0, 2.0),
    "gamma_exhaust": (1.0, 2.0),
    "adiabatic_flame_temperature": (0.0, 5000.0),
    "molecular_weight_chamber": (0.001, 0.200),
    "molecular_weight_exhaust": (0.001, 0.200),
    "i_sp_frozen": (0.0, 600.0),
    "i_sp_shifting": (0.0, 600.0),
    "qsi_chamber": (0.0, 1.0),
    "qsi_exhaust": (0.0, 1.0),
}


@dataclasses.dataclass(frozen=True, kw_only=True)
class ThermochemicalProperties:
    """Thermochemical properties for the combustion products of chemical rocket
    propellants.

    Attributes:
        gamma_chamber: Isentropic exponent in chamber (dimensionless).
        gamma_exhaust: Isentropic exponent at nozzle exit (dimensionless).
        adiabatic_flame_temperature: Ideal combustion temperature [K].
        molecular_weight_chamber: Molecular weight in chamber [kg/mol].
        molecular_weight_exhaust: Molecular weight at exit [kg/mol].
        i_sp_frozen: Frozen flow specific impulse [s].
        i_sp_shifting: Shifting equilibrium specific impulse [s].
        qsi_chamber: Condensed phase species content in chamber [mol/(100g)].
        qsi_exhaust: Condensed phase species content at exit [mol/(100g)].

    Raises:
        ValueError: If any parameter is outside a valid range.
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
        # Typical bounds in VALIDATION_BOUNDS
        for field_name, value in self.__dict__.items():
            if field_name in VALIDATION_BOUNDS:
                min_val, max_val = VALIDATION_BOUNDS[field_name]
                if not (min_val <= value <= max_val):
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

    @functools.cached_property
    def R_chamber(self) -> float:
        """Specific gas constant for chamber.

        Returns:
            float: Specific gas constant [J/(kg-K)].
        """
        return scipy.constants.R / self.molecular_weight_chamber

    @functools.cached_property
    def R_exhaust(self) -> float:
        """Specific gas constant for exhaust.

        Returns:
            float: Specific gas constant [J/(kg-K)].
        """
        return scipy.constants.R / self.molecular_weight_exhaust

    @functools.cached_property
    def is_two_phase_flow(self) -> bool:
        """Checks if combustion products have condensed phase species.

        Returns:
            bool: True if qsi_chamber > 0 or qsi_exhaust > 0.
        """
        return self.qsi_chamber > 0.0 or self.qsi_exhaust > 0.0
