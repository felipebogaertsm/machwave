"""Biliquid propellant type class."""

from typing import TYPE_CHECKING

import scipy.constants

if TYPE_CHECKING:
    from machwave.services import RocketCEAService

from ..properties import ThermochemicalProperties
from .base import Propellant


class BiliquidPropellant(Propellant):
    """Biliquid propellant composition.

    Stores a specific oxidizer/fuel combination and O/F ratio, and can calculate
    thermochemical properties using RocketCEA.

    Attributes:
        oxidizer_name: Oxidizer name as recognized by RocketCEA (e.g., "LOX", "N2O4").
        fuel_name: Fuel name as recognized by RocketCEA (e.g., "LH2", "RP1").
        of_ratio: Oxidizer-to-fuel mass ratio (dimensionless).
        properties: Calculated thermochemical properties (populated by evaluate).
        oxidizer_tank_density: Oxidizer storage density [kg/m³] (populated by evaluate).
        fuel_tank_density: Fuel storage density [kg/m³] (populated by evaluate).
    """

    def __init__(
        self,
        oxidizer_name: str,
        fuel_name: str,
        of_ratio: float,
        combustion_efficiency: float = 0.98,
        thermochem_service: "RocketCEAService | None" = None,
    ):
        """Initialize the BiliquidPropellant composition.

        Args:
            oxidizer_name: Oxidizer name recognized by RocketCEA.
            fuel_name: Fuel name recognized by RocketCEA.
            of_ratio: Oxidizer-to-fuel mass ratio.
            combustion_efficiency: Scaling factor (0 to 1) applied to ideal temperature.
            thermochem_service: Thermochemical service for calculations (default: RocketCEAService).
        """
        super().__init__(combustion_efficiency)
        self.oxidizer_name = oxidizer_name
        self.fuel_name = fuel_name
        self.of_ratio = of_ratio
        self.properties = None
        self.thermochem_service = thermochem_service

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> ThermochemicalProperties:
        """Calculate propellant properties using thermochemical service.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area expansion ratio (Ae/At).

        Returns:
            ThermochemicalProperties: Calculated propellant properties.
        """
        # Create service instance for this propellant
        if self.thermochem_service is None:
            from machwave.services import create_cea_service

            service = create_cea_service(
                oxidizer_name=self.oxidizer_name,
                fuel_name=self.fuel_name,
                oxidizer_to_fuel_ratio=self.of_ratio,
            )
        else:
            service = self.thermochem_service

        # Get thermochemical properties
        adiabatic_flame_temperature = service.get_adiabatic_flame_temperature(
            chamber_pressure=chamber_pressure
        )

        molecular_weight_chamber, gamma_chamber = service.get_chamber_properties(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        molecular_weight_exhaust, gamma_exhaust = service.get_exhaust_properties(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        i_sp_frozen, i_sp_shifting = service.get_specific_impulse(
            chamber_pressure=chamber_pressure, expansion_ratio=expansion_ratio
        )

        # Construct liquid propellant properties
        self.properties = ThermochemicalProperties(
            gamma_chamber=gamma_chamber,
            gamma_exhaust=gamma_exhaust,
            adiabatic_flame_temperature=adiabatic_flame_temperature,
            molecular_weight_chamber=molecular_weight_chamber,
            molecular_weight_exhaust=molecular_weight_exhaust,
            i_sp_frozen=i_sp_frozen,
            i_sp_shifting=i_sp_shifting,
            qsi_chamber=0.0,  # Liquid propellants produce gas-only combustion
            qsi_exhaust=0.0,
        )

        # Get tank densities
        oxidizer_density, fuel_density = service.get_tank_densities()
        self.oxidizer_tank_density = oxidizer_density
        self.fuel_tank_density = fuel_density

        return self.properties

    def update_properties(
        self, chamber_pressure: float, eps: float = 8.0, frozen: int = 0
    ) -> ThermochemicalProperties:
        """Backward compatibility method for updating properties.

        This method calls evaluate() internally. The 'frozen' parameter is ignored
        as evaluate() calculates both frozen and shifting properties.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            eps: Nozzle area expansion ratio (Ae/At).
            frozen: Ignored for backward compatibility.

        Returns:
            ThermochemicalProperties: Calculated propellant properties.
        """
        return self.evaluate(chamber_pressure=chamber_pressure, expansion_ratio=eps)

    def combustion_temperature(self) -> float:
        """Calculate real combustion temperature applying combustion efficiency.

        Returns:
            float: Real combustion temperature [K].

        Raises:
            ValueError: If properties have not been evaluated yet.
        """
        if self.properties is None:
            raise ValueError(
                "Must call evaluate() before accessing combustion_temperature"
            )
        return self.properties.adiabatic_flame_temperature * self.combustion_efficiency

    def get_c_star(self) -> float:
        """Compute characteristic velocity (c*) of the propellant.

        The characteristic velocity is a key performance parameter defined by:
            c* = sqrt((R * T_c) / gamma) * ((gamma+1)/2)^((gamma+1)/(2*(gamma-1)))
        where T_c is the combustion temperature (adjusted for efficiency) [K],
        R is the specific gas constant for the chamber [J/(kg·K)],
        and gamma is the isentropic exponent in the chamber.

        Returns:
            float: Characteristic velocity [m/s].
        """
        # Use the chamber conditions from properties
        assert self.properties is not None
        T_c = self.combustion_temperature()  # Apply combustion efficiency
        R_ch = scipy.constants.R / self.properties.molecular_weight_chamber
        gamma = self.properties.gamma_chamber

        # Calculate the factor based on the isentropic exponent
        factor = ((gamma + 1) / 2) ** ((gamma + 1) / (2 * (gamma - 1)))
        c_star = (R_ch * T_c / gamma) ** 0.5 * factor
        return c_star
