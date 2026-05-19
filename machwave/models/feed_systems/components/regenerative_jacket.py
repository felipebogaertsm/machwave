"""Regenerative-jacket specification dataclass shared by expander and staged-combustion cycles."""

import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class RegenerativeJacketSpec:
    """Static description of a regenerative cooling jacket around the chamber and nozzle.

    Expander and staged-combustion cycles route one propellant through a
    cooling jacket to absorb heat from the combustion chamber and nozzle walls.
    The fields below describe the design-point operating condition the cycle
    integrator can lean on when sizing downstream turbomachinery.

    Attributes:
        name: Human-readable identifier used in logs and reports.
        pressure_drop: Total coolant pressure drop across the jacket [Pa]. Must
            be non-negative.
        coolant_temperature_rise: Coolant total-temperature rise from jacket
            inlet to outlet [K]. Must be strictly positive.
        heat_pickup: Heat power absorbed by the coolant across the jacket [W].
            Must be non-negative.

    Raises:
        ValueError: If any field is outside its valid physical range.
    """

    name: str
    pressure_drop: float
    coolant_temperature_rise: float
    heat_pickup: float

    def __post_init__(self) -> None:
        """Validate that every field lies in its physical range."""
        if self.pressure_drop < 0.0:
            raise ValueError(
                f"pressure_drop must be non-negative, got {self.pressure_drop}"
            )
        if self.coolant_temperature_rise <= 0.0:
            raise ValueError(
                "coolant_temperature_rise must be strictly positive, "
                f"got {self.coolant_temperature_rise}"
            )
        if self.heat_pickup < 0.0:
            raise ValueError(
                f"heat_pickup must be non-negative, got {self.heat_pickup}"
            )
