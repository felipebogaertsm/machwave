"""Pump specification dataclass shared by turbopump-based feed-system cycles."""

import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class PumpSpec:
    """Static description of a propellant pump used by turbopump cycles.

    The values describe the pump at its design point. Cycle implementations
    consume these together with operating-point data (mass flow, density,
    rotational speed) to compute the actual head rise and power draw.

    Attributes:
        name: Human-readable identifier used in logs and reports.
        isentropic_efficiency: Ratio of isentropic enthalpy rise to actual
            enthalpy rise (dimensionless). Must lie in the half-open interval
            `(0, 1]`.
        pressure_rise: Design-point pressure rise across the pump [Pa]. Must
            be strictly positive.
        volumetric_flow_design: Design-point volumetric flow through the pump
            [m^3/s]. Must be strictly positive.
        shaft_speed_design: Design-point shaft angular speed [rad/s]. Must be
            strictly positive.

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
