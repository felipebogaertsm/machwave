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
        adiabatic_flame_temperature (float): Effective combustion temperature [K].
        adiabatic_flame_temperature_ideal (float): Theoretical combustion
            temperature [K].
        molecular_weight_chamber (float): Average molecular weight in chamber [kg/mol].
        molecular_weight_exhaust (float): Average molecular weight at exit [kg/mol].
        i_sp_frozen (float): Frozen flow specific impulse [s].
        i_sp_shifting (float): Shifting equilibrium specific impulse [s].
    """

    gamma_chamber: float
    gamma_exhaust: float
    adiabatic_flame_temperature: float
    adiabatic_flame_temperature_ideal: float
    molecular_weight_chamber: float
    molecular_weight_exhaust: float
    i_sp_frozen: float
    i_sp_shifting: float

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
        density (float): Propellant density [kg/m³].
        qsi_chamber (float): Condensed-phase species content in chamber [mol/(100g)].
        qsi_exhaust (float): Condensed-phase species content in exhaust [mol/(100g)].
    """

    density: float = dataclasses.field(kw_only=True)
    qsi_chamber: float = dataclasses.field(kw_only=True)
    qsi_exhaust: float = dataclasses.field(kw_only=True)


@dataclasses.dataclass(frozen=True)
class LiquidPropellantProperties(ChemicalPropellantProperties):
    """Liquid propellant properties."""
