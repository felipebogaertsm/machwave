import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class GasGeneratorSpec:
    """Gas generator driving a turbopump turbine.

    Attributes:
        name: Identifier used in logs and reports.
        mixture_ratio: Oxidizer to fuel mass ratio in the gas generator (>0).
        chamber_pressure: Combustion chamber pressure of the gas generator [Pa] (>0).
        gas_temperature: Combustion total temperature delivered to the turbine inlet
            [K] (>0).
        mass_flow: Total propellant mass flow through the gas generator [kg/s] (>0).

    Raises:
        ValueError: If any field is outside its valid physical range.
    """

    name: str
    mixture_ratio: float
    chamber_pressure: float
    gas_temperature: float
    mass_flow: float

    def __post_init__(self) -> None:
        """Validate that every field lies in its physical range."""
        if self.mixture_ratio <= 0.0:
            raise ValueError(
                f"mixture_ratio must be strictly positive, got {self.mixture_ratio}"
            )
        if self.chamber_pressure <= 0.0:
            raise ValueError(
                "chamber_pressure must be strictly positive, "
                f"got {self.chamber_pressure}"
            )
        if self.gas_temperature <= 0.0:
            raise ValueError(
                f"gas_temperature must be strictly positive, got {self.gas_temperature}"
            )
        if self.mass_flow <= 0.0:
            raise ValueError(
                f"mass_flow must be strictly positive, got {self.mass_flow}"
            )
