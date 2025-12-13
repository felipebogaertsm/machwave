"""Thermochemical properties of chemical propellants."""

import abc
import dataclasses

import scipy.constants


@dataclasses.dataclass(frozen=True)
class ChemicalPropellantProperties(abc.ABC):
    """Base abstract class for chemical propellant thermochemical properties.

    Args:
        gamma_chamber (float): Isentropic exponent in chamber (dimensionless).
        gamma_exhaust (float): Isentropic exponent at nozzle exit (dimensionless).
        adiabatic_flame_temperature (float): Ideal adiabatic flame temperature [K].
        combustion_efficiency (float): Combustion efficiency (0 to 1).
        molecular_weight_chamber (float): Average molecular weight in chamber [kg/mol].
        molecular_weight_exhaust (float): Average molecular weight at exit [kg/mol].
        i_sp_frozen (float): Frozen flow specific impulse [s].
        i_sp_shifting (float): Shifting equilibrium specific impulse [s].

    Properties:
        combustion_temperature (float): Real combustion temperature [K].
        R_chamber (float): Specific gas constant for chamber [J/(kg·K)].
        R_exhaust (float): Specific gas constant for nozzle exit [J/(kg·K)].
    """

    gamma_chamber: float
    gamma_exhaust: float
    adiabatic_flame_temperature: float
    combustion_efficiency: float
    molecular_weight_chamber: float
    molecular_weight_exhaust: float
    i_sp_frozen: float
    i_sp_shifting: float

    @property
    def combustion_temperature(self) -> float:
        """Real combustion temperature, determined by the adiabatic flame temperature
        multiplied by the combustion efficiency.

        Returns:
            float: Real combustion temperature [K].
        """
        return self.adiabatic_flame_temperature * self.combustion_efficiency

    @property
    def R_chamber(self) -> float:
        """Specific gas constant for chamber.

        Returns:
            float: Specific gas constant [J/(kg·K)].
        """
        return scipy.constants.R / self.molecular_weight_chamber

    @property
    def R_exhaust(self) -> float:
        """Specific gas constant for nozzle exit.

        Returns:
            float: Specific gas constant [J/(kg·K)].
        """
        return scipy.constants.R / self.molecular_weight_exhaust


@dataclasses.dataclass(frozen=True)
class SolidPropellantProperties(ChemicalPropellantProperties):
    """Solid propellant properties.

    Args:
        density (float): Solid propellant density [kg/m³].
        qsi_chamber (float): Condensed-phase species content in chamber [mol/(100g)].
        qsi_exhaust (float): Condensed-phase species content in exhaust [mol/(100g)].
    """

    density: float = dataclasses.field(kw_only=True)
    qsi_chamber: float = dataclasses.field(kw_only=True)
    qsi_exhaust: float = dataclasses.field(kw_only=True)


@dataclasses.dataclass(frozen=True)
class LiquidPropellantProperties(ChemicalPropellantProperties):
    """Liquid propellant properties."""
