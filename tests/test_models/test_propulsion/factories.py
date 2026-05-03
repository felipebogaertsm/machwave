"""Test factories for propulsion propellant properties.

This module provides polyfactory-based factories for generating test instances
of propellant property dataclasses with realistic default values.
"""

from polyfactory.factories import DataclassFactory

from machwave.models.propellants.properties import (
    ThermochemicalProperties,
)


class SolidPropellantPropertiesFactory(DataclassFactory[ThermochemicalProperties]):
    """Factory for creating ThermochemicalProperties test instances for solid propellants.

    Uses polyfactory to generate realistic test data with sensible defaults.
    All fields can be overridden by passing them to build() or batch().

    Example:
        # Use default values
        props = SolidPropellantPropertiesFactory.build()

        # Override specific fields
        props = SolidPropellantPropertiesFactory.build(
            k_chamber=1.20,
            density=1850.0
        )

        # Create multiple instances
        props_list = SolidPropellantPropertiesFactory.batch(size=10)
    """

    __model__ = ThermochemicalProperties

    @classmethod
    def k_chamber(cls) -> float:
        """Typical isentropic exponent in chamber (1.1-1.3 for solid propellants)."""
        return 1.15

    @classmethod
    def k_exhaust(cls) -> float:
        """Typical isentropic exponent at exit (slightly lower than chamber)."""
        return 1.10

    @classmethod
    def adiabatic_flame_temperature(cls) -> float:
        """Typical ideal adiabatic flame temperature in Kelvin."""
        return 3200.0

    @classmethod
    def combustion_efficiency(cls) -> float:
        """Typical combustion efficiency (0-1)."""
        return 0.95

    @classmethod
    def molecular_weight_chamber(cls) -> float:
        """Typical molecular weight in kg/mol for chamber gases."""
        return 0.04

    @classmethod
    def molecular_weight_exhaust(cls) -> float:
        """Typical molecular weight in kg/mol for exhaust gases."""
        return 0.041

    @classmethod
    def i_sp_frozen(cls) -> float:
        """Typical frozen specific impulse in seconds."""
        return 250.0

    @classmethod
    def i_sp_shifting(cls) -> float:
        """Typical shifting equilibrium Isp in seconds (≥ frozen)."""
        return 255.0

    @classmethod
    def density(cls) -> float:
        """Typical solid propellant density in kg/m³."""
        return 1800.0

    @classmethod
    def qsi_chamber(cls) -> float:
        """Typical condensed phase mole fraction in chamber [mol/(100g)]."""
        return 0.3

    @classmethod
    def qsi_exhaust(cls) -> float:
        """Typical condensed phase mole fraction in exhaust [mol/(100g)]."""
        return 0.32


class LiquidPropellantPropertiesFactory(DataclassFactory[ThermochemicalProperties]):
    """Factory for creating ThermochemicalProperties test instances for liquid propellants.

    Uses polyfactory to generate realistic test data with sensible defaults.
    All fields can be overridden by passing them to build() or batch().

    Example:
        # Use default values
        props = LiquidPropellantPropertiesFactory.build()

        # Override specific fields
        props = LiquidPropellantPropertiesFactory.build(
            k_chamber=1.25,
            i_sp_frozen=320.0
        )

        # Create multiple instances
        props_list = LiquidPropellantPropertiesFactory.batch(size=10)
    """

    __model__ = ThermochemicalProperties

    @classmethod
    def k_chamber(cls) -> float:
        """Typical isentropic exponent in chamber (1.15-1.25 for liquid propellants)."""
        return 1.20

    @classmethod
    def k_exhaust(cls) -> float:
        """Typical isentropic exponent at exit."""
        return 1.15

    @classmethod
    def adiabatic_flame_temperature(cls) -> float:
        """Typical ideal adiabatic flame temperature in Kelvin."""
        return 3600.0

    @classmethod
    def combustion_efficiency(cls) -> float:
        """Typical combustion efficiency (0-1)."""
        return 0.95

    @classmethod
    def molecular_weight_chamber(cls) -> float:
        """Typical molecular weight in kg/mol for chamber gases."""
        return 0.02

    @classmethod
    def molecular_weight_exhaust(cls) -> float:
        """Typical molecular weight in kg/mol for exhaust gases."""
        return 0.021

    @classmethod
    def i_sp_frozen(cls) -> float:
        """Typical frozen specific impulse in seconds."""
        return 300.0

    @classmethod
    def i_sp_shifting(cls) -> float:
        """Typical shifting equilibrium Isp in seconds."""
        return 310.0

    @classmethod
    def qsi_chamber(cls) -> float:
        """Liquid propellants produce gas-only combustion (no condensed phase)."""
        return 0.0

    @classmethod
    def qsi_exhaust(cls) -> float:
        """Liquid propellants produce gas-only combustion (no condensed phase)."""
        return 0.0
