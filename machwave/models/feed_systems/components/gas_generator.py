"""Gas-generator specification dataclass shared by gas-generator-cycle feed systems."""

import dataclasses

GAS_TEMPERATURE_MINIMUM_KELVIN = 300.0
GAS_TEMPERATURE_MAXIMUM_KELVIN = 1500.0


@dataclasses.dataclass(frozen=True, kw_only=True)
class GasGeneratorSpec:
    """Static description of a gas generator driving a turbopump turbine.

    A gas generator burns a small fraction of the propellants at a low mixture
    ratio so the resulting working fluid stays below turbine metal limits. The
    fields below describe the combustion product stream delivered to the
    turbine inlet at the design point.

    Attributes:
        name: Human-readable identifier used in logs and reports.
        mixture_ratio: Oxidizer-to-fuel mass ratio in the gas generator
            (dimensionless). Must be strictly positive.
        chamber_pressure: Combustion chamber pressure of the gas generator
            [Pa]. Must be strictly positive.
        gas_temperature: Combustion-product total temperature delivered to the
            turbine inlet [K]. Must lie in
            `[GAS_TEMPERATURE_MINIMUM_KELVIN, GAS_TEMPERATURE_MAXIMUM_KELVIN]`
            to stay below typical uncooled turbine blade limits.
        mass_flow: Total propellant mass flow through the gas generator
            [kg/s]. Must be strictly positive.

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
        if not (
            GAS_TEMPERATURE_MINIMUM_KELVIN
            <= self.gas_temperature
            <= GAS_TEMPERATURE_MAXIMUM_KELVIN
        ):
            raise ValueError(
                "gas_temperature must be in the interval "
                f"[{GAS_TEMPERATURE_MINIMUM_KELVIN}, "
                f"{GAS_TEMPERATURE_MAXIMUM_KELVIN}] K, got {self.gas_temperature}"
            )
        if self.mass_flow <= 0.0:
            raise ValueError(
                f"mass_flow must be strictly positive, got {self.mass_flow}"
            )
