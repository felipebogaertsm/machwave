import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class PumpSpec:
    """
    Propellant pump used by turbopump cycles.

    Attributes:
        name: Identifier used in logs and reports.
        isentropic_efficiency: Ratio of isentropic enthalpy rise to actual
            enthalpy rise. Must lie between 0 and 1.
        pressure_rise: Pressure rise across the pump [Pa] (>0).
        volumetric_flow_design: Volumetric flow through the pump
            [m^3/s] (>0).
        shaft_speed_design: Shaft angular speed [rad/s] (>0).

    Raises:
        ValueError: If any field is outside its valid physical range.
    """

    name: str
    isentropic_efficiency: float
    pressure_rise: float
    volumetric_flow_design: float
    shaft_speed_design: float

    def __post_init__(self) -> None:
        """Validate that every field lies in its physical range."""
        if not (0.0 < self.isentropic_efficiency <= 1.0):
            raise ValueError(
                "isentropic_efficiency must be in the interval (0, 1], "
                f"got {self.isentropic_efficiency}"
            )
        if self.pressure_rise <= 0.0:
            raise ValueError(
                f"pressure_rise must be strictly positive, got {self.pressure_rise}"
            )
        if self.volumetric_flow_design <= 0.0:
            raise ValueError(
                "volumetric_flow_design must be strictly positive, "
                f"got {self.volumetric_flow_design}"
            )
        if self.shaft_speed_design <= 0.0:
            raise ValueError(
                "shaft_speed_design must be strictly positive, "
                f"got {self.shaft_speed_design}"
            )
