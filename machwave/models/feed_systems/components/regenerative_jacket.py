import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class RegenerativeJacketSpec:
    """Regenerative cooling component around the chamber and nozzle.

    Attributes:
        name: Identifier used in logs and reports.
        pressure_drop: Total coolant pressure drop across the jacket [Pa] (>0).
        coolant_temperature_rise: Coolant total temperature rise from jacket
            inlet to outlet [K] (>0).
        heat_pickup: Heat power absorbed by the coolant across the jacket [W] (>=0).

    Raises:
        ValueError: If any field is outside its valid physical range.
    """

    name: str
    pressure_drop: float
    coolant_temperature_rise: float
    heat_pickup: float

    def __post_init__(self) -> None:
        """Validate that every field lies in its physical range."""
        if self.pressure_drop <= 0.0:
            raise ValueError(
                f"pressure_drop must be strictly positive, got {self.pressure_drop}"
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
