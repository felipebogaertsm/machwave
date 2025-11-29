"""Biliquid propellant type class."""

import scipy.constants
from rocketcea.cea_obj import CEA_Obj

from machwave.core.conversions import (
    convert_lbft3_to_kgm3,
    convert_pa_to_psi,
    convert_rankine_to_kelvin,
)

from ..properties import LiquidPropellantProperties
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
    ):
        """Initialize the BiliquidPropellant composition.

        Args:
            oxidizer_name: Oxidizer name recognized by RocketCEA.
            fuel_name: Fuel name recognized by RocketCEA.
            of_ratio: Oxidizer-to-fuel mass ratio.
            combustion_efficiency: Scaling factor (0 to 1) applied to ideal temperature.
        """
        super().__init__(combustion_efficiency)
        self.oxidizer_name = oxidizer_name
        self.fuel_name = fuel_name
        self.of_ratio = of_ratio
        self.properties = None

    def evaluate(
        self, chamber_pressure: float, expansion_ratio: float = 8.0
    ) -> LiquidPropellantProperties:
        """Calculate propellant properties using RocketCEA.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            expansion_ratio: Nozzle area expansion ratio (Ae/At).

        Returns:
            LiquidPropellantProperties: Calculated propellant properties.
        """
        # Create CEA object for this propellant combination
        self.cea_obj = CEA_Obj(oxName=self.oxidizer_name, fuelName=self.fuel_name)

        # Convert pressure to psi for RocketCEA
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        # Combustion temperature
        adiabatic_flame_temperature_ideal = convert_rankine_to_kelvin(
            self.cea_obj.get_Tcomb(Pc=chamber_pressure_psi, MR=self.of_ratio)
        )
        adiabatic_flame_temperature = (
            adiabatic_flame_temperature_ideal * self.combustion_efficiency
        )

        # Get propellant liquid densities (operational/storage properties)
        oxidizer_tank_density_lbft3, fuel_tank_density_lbft3 = (
            self.cea_obj.get_OxFuelDensities()
        )
        self.oxidizer_tank_density = convert_lbft3_to_kgm3(oxidizer_tank_density_lbft3)
        self.fuel_tank_density = convert_lbft3_to_kgm3(fuel_tank_density_lbft3)

        # Chamber properties
        molecular_weight_chamber_g, gamma_chamber = (
            self.cea_obj.get_Chamber_MolWt_gamma(
                Pc=chamber_pressure_psi, MR=self.of_ratio, eps=expansion_ratio
            )
        )
        molecular_weight_chamber = (
            molecular_weight_chamber_g / 1000.0
        )  # g/mol -> kg/mol

        # Exit properties (frozen flow)
        molecular_weight_exhaust_g, gamma_exhaust = self.cea_obj.get_exit_MolWt_gamma(
            Pc=chamber_pressure_psi, MR=self.of_ratio, eps=expansion_ratio, frozen=1
        )
        molecular_weight_exhaust = (
            molecular_weight_exhaust_g / 1000.0
        )  # g/mol -> kg/mol

        # Specific impulse
        i_sp_frozen = self.cea_obj.get_Isp(
            Pc=chamber_pressure_psi,
            MR=self.of_ratio,
            eps=expansion_ratio,
            frozen=1,
        )
        i_sp_shifting = self.cea_obj.get_Isp(
            Pc=chamber_pressure_psi,
            MR=self.of_ratio,
            eps=expansion_ratio,
            frozen=0,
        )

        # Create and store properties object
        self.properties = LiquidPropellantProperties(
            gamma_chamber=gamma_chamber,
            gamma_exhaust=gamma_exhaust,
            adiabatic_flame_temperature=adiabatic_flame_temperature,
            molecular_weight_chamber=molecular_weight_chamber,
            molecular_weight_exhaust=molecular_weight_exhaust,
            i_sp_frozen=i_sp_frozen,
            i_sp_shifting=i_sp_shifting,
            adiabatic_flame_temperature_ideal=adiabatic_flame_temperature_ideal,
        )

        return self.properties

    def update_properties(
        self, chamber_pressure: float, eps: float = 8.0, frozen: int = 0
    ) -> LiquidPropellantProperties:
        """Backward compatibility method for updating properties.

        This method calls evaluate() internally. The 'frozen' parameter is ignored
        as evaluate() calculates both frozen and shifting properties.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            eps: Nozzle area expansion ratio (Ae/At).
            frozen: Ignored for backward compatibility.

        Returns:
            LiquidPropellantProperties: Calculated propellant properties.
        """
        return self.evaluate(chamber_pressure=chamber_pressure, expansion_ratio=eps)

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
        T_c = self.properties.adiabatic_flame_temperature
        R_ch = scipy.constants.R / self.properties.molecular_weight_chamber
        gamma = self.properties.gamma_chamber

        # Calculate the factor based on the isentropic exponent
        factor = ((gamma + 1) / 2) ** ((gamma + 1) / (2 * (gamma - 1)))
        c_star = (R_ch * T_c / gamma) ** 0.5 * factor
        return c_star
