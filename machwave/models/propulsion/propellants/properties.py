import abc
import dataclasses

import scipy.constants


@dataclasses.dataclass(frozen=True)
class ChemicalPropellantProperties(abc.ABC):
    """Base abstract class for chemical propellant properties. Stores thermochemical
    properties that are common to all chemical propellants.

    Attributes:
        gamma_chamber: Isentropic exponent in chamber (dimensionless).
        gamma_exhaust: Isentropic exponent at nozzle exit (dimensionless).
        adiabatic_flame_temperature: Effective combustion temperature [K].
        adiabatic_flame_temperature_ideal: Theoretical combustion temperature [K].
        molecular_weight_chamber: Average molecular weight in chamber [kg/mol].
        molecular_weight_exhaust: Average molecular weight at exit [kg/mol].
        i_sp_frozen: Frozen flow specific impulse [s].
        i_sp_shifting: Shifting equilibrium specific impulse [s].
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
        """Calculate specific gas constant for chamber [J/(kg·K)].

        Returns:
            Specific gas constant derived from universal gas constant
            and chamber molecular weight.
        """
        return scipy.constants.R / self.molecular_weight_chamber

    @property
    def R_exhaust(self) -> float:
        """Calculate specific gas constant for nozzle exit [J/(kg·K)].

        Returns:
            Specific gas constant derived from universal gas constant
            and exhaust molecular weight.
        """
        return scipy.constants.R / self.molecular_weight_exhaust


@dataclasses.dataclass(frozen=True)
class SolidPropellantProperties(ChemicalPropellantProperties):
    """Properties container for solid propellants.

    Extends ChemicalPropellantProperties with solid-propellant-specific properties.

    Attributes:
        density: Propellant density [kg/m³].
        qsi_chamber: Condensed-phase species content in chamber [mol/(100g)].
        qsi_exhaust: Condensed-phase species content in exhaust [mol/(100g)].
    """

    density: float = dataclasses.field(kw_only=True)
    qsi_chamber: float = dataclasses.field(kw_only=True)
    qsi_exhaust: float = dataclasses.field(kw_only=True)


@dataclasses.dataclass(frozen=True)
class LiquidPropellantProperties(ChemicalPropellantProperties):
    """Properties container for liquid propellants.

    Extends ChemicalPropellantProperties with liquid-propellant-specific properties.

    Attributes:
        oxidizer_tank_density: Liquid oxidizer tank density [kg/m³].
        fuel_tank_density: Liquid fuel tank density [kg/m³].
    """

    oxidizer_tank_density: float = dataclasses.field(kw_only=True)
    fuel_tank_density: float = dataclasses.field(kw_only=True)
