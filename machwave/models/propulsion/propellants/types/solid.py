"""Solid propellant type classes."""

from rocketcea.cea_obj import CEA_Obj

from machwave.core.conversions import (
    convert_pa_to_psi,
    convert_rankine_to_kelvin,
)

from ..properties import SolidPropellantProperties
from .base import BurnRateOutOfBoundsError, Propellant


class SolidPropellant(Propellant):
    """Base class for solid propellants.

    Provides common interface for solid propellant burn rate calculations.

    Attributes:
        burn_rate: List of dictionaries describing burn rate behavior (St.
            Robert's law parameters) with keys: "min", "max", "a", and "n".
    """

    def __init__(
        self,
        burn_rate: list[dict[str, float | int]],
        combustion_efficiency: float = 0.95,
    ):
        super().__init__(combustion_efficiency)
        self.burn_rate = burn_rate

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """Calculate instantaneous burn rate using St. Robert's law.

        Args:
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            float: Burn rate [m/s].

        Raises:
            BurnRateOutOfBoundsError: If chamber pressure is outside valid range.
        """
        for item in self.burn_rate:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                # Convert pressure from Pa to MPa, apply St. Robert's law,
                # then convert from mm/s to m/s
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3

        raise BurnRateOutOfBoundsError(chamber_pressure)


class FixedSolidPropellant(SolidPropellant):
    """Solid propellant with pre-defined thermochemical properties.

    Used for propellants with empirical data from literature or testing.
    Properties are immutable after initialization.

    Args:
        name: Propellant name for identification.
        burn_rate: Burn rate parameters (St. Robert's law).
        properties: Thermochemical properties.
        combustion_efficiency: Combustion efficiency (0 to 1).
    """

    def __init__(
        self,
        name: str,
        burn_rate: list[dict[str, float | int]],
        properties: SolidPropellantProperties,
        combustion_efficiency: float = 0.95,
    ):
        super().__init__(burn_rate, combustion_efficiency)
        self.name = name
        self.properties = properties

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> SolidPropellantProperties:
        """Return pre-defined properties (no calculation needed).

        Args:
            chamber_pressure: Chamber pressure [Pa] (unused for fixed propellants).
            expansion_ratio: Nozzle area ratio (unused for fixed propellants).

        Returns:
            SolidPropellantProperties: Pre-defined thermochemical properties.
        """
        return self.properties


class CEASolidPropellant(SolidPropellant):
    """Solid propellant with CEA-calculated thermochemical properties.

    Dynamically calculates properties using RocketCEA at specified operating conditions.

    Args:
        cea_name: Propellant name as recognized by RocketCEA.
        burn_rate: Burn rate parameters (St. Robert's law).
        ideal_density: Theoretical propellant density [kg/m³].
        density_percentage: Percentage of theoretical density achieved (0-100).
            Accounts for manufacturing imperfections and voids.
        combustion_efficiency: Combustion efficiency (0 to 1).
    """

    def __init__(
        self,
        cea_name: str,
        burn_rate: list[dict[str, float | int]],
        ideal_density: float,
        density_percentage: float = 98.0,
        combustion_efficiency: float = 0.95,
    ):
        super().__init__(burn_rate, combustion_efficiency)
        self.cea_name = cea_name
        self.ideal_density = ideal_density
        self.density_percentage = density_percentage

    def real_density(self) -> float:
        """Calculate actual propellant density accounting for manufacturing imperfections.

        Returns:
            float: Real density [kg/m³] calculated as ideal_density * (density_percentage/100).
        """
        return self.ideal_density * (self.density_percentage / 100.0)

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> SolidPropellantProperties:
        """Calculate thermochemical properties using RocketCEA.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area ratio (Ae/At).

        Returns:
            SolidPropellantProperties: Calculated thermochemical properties.
        """
        cea_obj = CEA_Obj(propName=self.cea_name)
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        # Combustion temperature
        adiabatic_flame_temperature_ideal = convert_rankine_to_kelvin(
            cea_obj.get_Tcomb(Pc=chamber_pressure_psi)
        )
        adiabatic_flame_temperature = (
            adiabatic_flame_temperature_ideal * self.combustion_efficiency
        )

        # Chamber properties
        molecular_weight_chamber_g, gamma_chamber = cea_obj.get_Chamber_MolWt_gamma(
            Pc=chamber_pressure_psi, eps=expansion_ratio
        )
        molecular_weight_chamber = (
            molecular_weight_chamber_g / 1000.0
        )  # g/mol -> kg/mol

        # Exit properties (frozen flow)
        molecular_weight_exhaust_g, gamma_exhaust = cea_obj.get_exit_MolWt_gamma(
            Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=1
        )
        molecular_weight_exhaust = (
            molecular_weight_exhaust_g / 1000.0
        )  # g/mol -> kg/mol

        # Specific impulse
        i_sp_frozen = cea_obj.get_Isp(
            Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=1
        )
        i_sp_shifting = cea_obj.get_Isp(
            Pc=chamber_pressure_psi, eps=expansion_ratio, frozen=0
        )

        self.properties = SolidPropellantProperties(
            gamma_chamber=gamma_chamber,
            gamma_exhaust=gamma_exhaust,
            adiabatic_flame_temperature=adiabatic_flame_temperature,
            adiabatic_flame_temperature_ideal=adiabatic_flame_temperature_ideal,
            molecular_weight_chamber=molecular_weight_chamber,
            molecular_weight_exhaust=molecular_weight_exhaust,
            i_sp_frozen=i_sp_frozen,
            i_sp_shifting=i_sp_shifting,
            density=self.real_density(),
            qsi_chamber=0.0,  # CEA doesn't provide condensed phase data directly
            qsi_exhaust=0.0,
        )

        return self.properties
