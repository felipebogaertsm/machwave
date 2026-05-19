"""Turbine specification dataclass shared by turbopump-based feed-system cycles."""

import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class TurbineSpec:
    """Static description of a turbine used by turbopump cycles.

    The values describe the turbine at its design point. Cycle implementations
    consume these together with the working-fluid conditions to compute the
    actual shaft power delivered to the coupled pump.

    Attributes:
        name: Human-readable identifier used in logs and reports.
        isentropic_efficiency: Ratio of actual specific work extracted to the
            isentropic specific work available across the turbine
            (dimensionless). Must lie in the half-open interval `(0, 1]`.
        pressure_ratio: Ratio of turbine inlet total pressure to outlet total
            pressure (dimensionless). Must be strictly greater than one.
        inlet_temperature_design: Design-point total temperature at the turbine
            inlet [K]. Must be strictly positive.
        mass_flow_design: Design-point mass flow through the turbine [kg/s].
            Must be strictly positive.

    Raises:
        ValueError: If any field is outside its valid physical range.
    """

    name: str
    isentropic_efficiency: float
    pressure_ratio: float
    inlet_temperature_design: float
    mass_flow_design: float

    def __post_init__(self) -> None:
        """Validate that every field lies in its physical range."""
        if not (0.0 < self.isentropic_efficiency <= 1.0):
            raise ValueError(
                "isentropic_efficiency must be in the interval (0, 1], "
                f"got {self.isentropic_efficiency}"
            )
        if self.pressure_ratio <= 1.0:
            raise ValueError(
                "pressure_ratio must be strictly greater than one, "
                f"got {self.pressure_ratio}"
            )
        if self.inlet_temperature_design <= 0.0:
            raise ValueError(
                "inlet_temperature_design must be strictly positive, "
                f"got {self.inlet_temperature_design}"
            )
        if self.mass_flow_design <= 0.0:
            raise ValueError(
                "mass_flow_design must be strictly positive, "
                f"got {self.mass_flow_design}"
            )
