import scipy.constants
from rocketcea.cea_obj import CEA_Obj

from machwave.services.conversions import (
    convert_lbft3_to_kgm3,
    convert_pa_to_psi,
    convert_rankine_to_kelvin,
)

from .base import Propellant


class BiliquidPropellant(Propellant):
    """
    Stores and manages liquid propellant data with RocketCEA integration.

    This class instantiates a RocketCEA object for a given oxidizer and fuel,
    then queries RocketCEA to compute thermochemical properties for the propellant
    (e.g., chamber density, molecular weight, isentropic exponent, etc.).

    Attributes:
        oxidizer_name:
            Name of the oxidizer as recognized by RocketCEA (e.g., "LOX", "N2O4").
        fuel_name:
            Name of the fuel as recognized by RocketCEA (e.g., "LH2", "RP1").
        of_ratio:
            Oxidizer-to-fuel mass ratio (dimensionless).
        combustion_efficiency:
            Overall combustion efficiency factor (0 to 1). The theoretical
            combustion temperature from RocketCEA is multiplied by this factor
            to approximate real-world losses.
        combustion_temperature_ideal:
            The theoretical combustion temperature from RocketCEA [K].
        combustion_temperature:
            The adjusted combustion temperature after accounting for
            `combustion_efficiency` [K].
        chamber_density:
            The density of the propellant gases in the chamber region [kg/m^3].
        chamber_molecular_weight:
            The average molecular weight in the chamber [kg/mol].
        exit_molecular_weight:
            The average molecular weight at the nozzle exit [kg/mol].
        chamber_gamma:
            The isentropic exponent (gamma) in the chamber region (dimensionless).
        exit_gamma:
            The isentropic exponent (gamma) at the nozzle exit (dimensionless).
        R_chamber:
            Specific gas constant for the chamber region [J/(kg·K)].
        R_exit:
            Specific gas constant for the nozzle exit [J/(kg·K)].
    """

    def __init__(
        self,
        oxidizer_name: str,
        fuel_name: str,
        of_ratio: float,
        combustion_efficiency: float = 0.98,
    ):
        """
        Initialize the BiliquidPropellant instance and update properties.

        Args:
            oxidizer_name:
                Name of the oxidizer recognized by RocketCEA.
            fuel_name:
                Name of the fuel recognized by RocketCEA.
            of_ratio:
                Oxidizer-to-fuel mass ratio.
            combustion_efficiency:
                Scaling factor (0 to 1) applied to the ideal combustion temperature.
                Defaults to 1.0 (no reduction).
        """
        self.oxidizer_name = oxidizer_name
        self.fuel_name = fuel_name
        self.of_ratio = of_ratio
        self.combustion_efficiency = combustion_efficiency

        # Initialize attributes that will be set by update_properties()
        self.combustion_temperature_ideal = 0.0
        self.combustion_temperature = 0.0
        self.chamber_density = 0.0
        self.chamber_molecular_weight = 0.0
        self.exit_molecular_weight = 0.0
        self.chamber_gamma = 0.0
        self.exit_gamma = 0.0
        self.R_chamber = 0.0
        self.R_exit = 0.0

        # Create the RocketCEA object
        self.cea_obj = CEA_Obj(oxName=self.oxidizer_name, fuelName=self.fuel_name)

        # Provide a default initial chamber pressure in Pascals
        self.update_properties(chamber_pressure=400.0)

    def update_properties(
        self, chamber_pressure: float, eps: float = 8.0, frozen: int = 0
    ):
        """
        Update propellant thermochemical properties using RocketCEA.

        Args:
            chamber_pressure:
                Chamber pressure in Pascals.
            eps:
                Nozzle area expansion ratio (Ae/At). Defaults to 8.0.
            frozen:
                Set to 1 to use the "frozen" flow assumption; 0 for "shifting" flow.
        """
        # 1) Convert from Pa to psi for RocketCEA
        chamber_pressure_psi = convert_pa_to_psi(chamber_pressure)

        # 2) Ideal combustion temperature from CEA
        self.combustion_temperature_ideal = convert_rankine_to_kelvin(
            self.cea_obj.get_Tcomb(Pc=chamber_pressure_psi, MR=self.of_ratio)
        )

        # 3) Apply combustion efficiency factor to approximate real Tcomb
        self.combustion_temperature = (
            self.combustion_temperature_ideal * self.combustion_efficiency
        )

        # 4) Get chamber density from CEA: (Chamber, Throat, Exit) => first value is chamber
        densities = self.cea_obj.get_Densities(
            Pc=chamber_pressure_psi, MR=self.of_ratio, eps=eps, frozen=frozen
        )  # in lb/ft^3
        self.chamber_density = convert_lbft3_to_kgm3(densities[0])

        # 5) Chamber molecular weight + gamma
        ch_molwt_g, ch_gamma = self.cea_obj.get_Chamber_MolWt_gamma(
            Pc=chamber_pressure_psi, MR=self.of_ratio, eps=eps
        )
        self.chamber_molecular_weight = ch_molwt_g / 1000.0  # Convert g/mol -> kg/mol
        self.chamber_gamma = ch_gamma

        # 6) Exit molecular weight + gamma
        ex_molwt_g, ex_gamma = self.cea_obj.get_exit_MolWt_gamma(
            Pc=chamber_pressure_psi, MR=self.of_ratio, eps=eps, frozen=frozen
        )
        self.exit_molecular_weight = ex_molwt_g / 1000.0
        self.exit_gamma = ex_gamma

        # 7) Gas constants at chamber & exit conditions
        self.R_chamber = scipy.constants.R / self.chamber_molecular_weight
        self.R_exit = scipy.constants.R / self.exit_molecular_weight

    def get_c_star(self) -> float:
        """
        Compute and return the characteristic velocity (c*) of the propellant.

        The characteristic velocity is a key performance parameter defined by:
            c* = sqrt((R * T_c) / gamma) * ((gamma+1)/2)^((gamma+1)/(2*(gamma-1)))
        where:
            T_c is the combustion temperature (adjusted for efficiency) [K],
            R is the specific gas constant for the chamber [J/(kg·K)],
            gamma is the isentropic exponent in the chamber.

        Returns:
            float: Characteristic velocity in m/s.
        """
        # Use the chamber conditions for calculation
        T_c = self.combustion_temperature
        R_ch = self.R_chamber
        gamma = self.chamber_gamma

        # Calculate the factor based on the isentropic exponent
        factor = ((gamma + 1) / 2) ** ((gamma + 1) / (2 * (gamma - 1)))
        c_star = (R_ch * T_c / gamma) ** 0.5 * factor
        return c_star
