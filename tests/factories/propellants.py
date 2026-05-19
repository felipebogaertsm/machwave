"""
ThermochemicalProperties uses polyfactory's DataclassFactory (the model is a
frozen, kw_only dataclass with strict validation bounds); the rest are plain
builders so chemical formulas stay deterministic rather than randomized.
"""

from __future__ import annotations

from typing import Any

from polyfactory.factories import DataclassFactory

from machwave.models.propellants import categories, components, properties


class SolidPropellantPropertiesFactory(
    DataclassFactory[properties.ThermochemicalProperties]
):
    __model__ = properties.ThermochemicalProperties

    @classmethod
    def k_chamber(cls) -> float:
        return 1.15

    @classmethod
    def k_exhaust(cls) -> float:
        return 1.10

    @classmethod
    def adiabatic_flame_temperature(cls) -> float:
        return 3200.0

    @classmethod
    def molecular_weight_chamber(cls) -> float:
        return 0.04

    @classmethod
    def molecular_weight_exhaust(cls) -> float:
        return 0.041

    @classmethod
    def i_sp_frozen(cls) -> float:
        return 250.0

    @classmethod
    def i_sp_shifting(cls) -> float:
        return 255.0

    @classmethod
    def qsi_chamber(cls) -> float:
        return 0.3

    @classmethod
    def qsi_exhaust(cls) -> float:
        return 0.32


class LiquidPropellantPropertiesFactory(
    DataclassFactory[properties.ThermochemicalProperties]
):
    """qsi values are zero — liquid combustion has no condensed phase."""

    __model__ = properties.ThermochemicalProperties

    @classmethod
    def k_chamber(cls) -> float:
        return 1.20

    @classmethod
    def k_exhaust(cls) -> float:
        return 1.15

    @classmethod
    def adiabatic_flame_temperature(cls) -> float:
        return 3600.0

    @classmethod
    def molecular_weight_chamber(cls) -> float:
        return 0.02

    @classmethod
    def molecular_weight_exhaust(cls) -> float:
        return 0.021

    @classmethod
    def i_sp_frozen(cls) -> float:
        return 300.0

    @classmethod
    def i_sp_shifting(cls) -> float:
        return 310.0

    @classmethod
    def qsi_chamber(cls) -> float:
        return 0.0

    @classmethod
    def qsi_exhaust(cls) -> float:
        return 0.0


class OxidizerComponentFactory:
    """Defaults to N2O."""

    @classmethod
    def build(cls, **overrides: Any) -> components.PropellantComponent:
        kwargs: dict[str, Any] = dict(
            name="N2O",
            role=components.ComponentRole.OXIDIZER,
            density=745.0,
            chemical_formula={"N": 2, "O": 1},
            enthalpy=0.0,
            initial_temperature=298.15,
        )
        kwargs.update(overrides)
        return components.PropellantComponent(**kwargs)


class FuelComponentFactory:
    """Defaults to Ethanol."""

    @classmethod
    def build(cls, **overrides: Any) -> components.PropellantComponent:
        kwargs: dict[str, Any] = dict(
            name="Ethanol",
            role=components.ComponentRole.FUEL,
            density=789.0,
            chemical_formula={"C": 2, "H": 6, "O": 1},
            enthalpy=0.0,
            initial_temperature=298.15,
        )
        kwargs.update(overrides)
        return components.PropellantComponent(**kwargs)


class BiliquidPropellantFactory:
    @classmethod
    def build(cls, **overrides: Any) -> categories.BiliquidPropellant:
        component_list = overrides.pop("components", None)
        if component_list is None:
            component_list = [
                OxidizerComponentFactory.build(),
                FuelComponentFactory.build(),
            ]
        kwargs: dict[str, Any] = dict(
            name="N2O/Ethanol",
            components=component_list,
            combustion_efficiency=0.98,
            oxidizer_to_fuel_ratio=2.0,
        )
        kwargs.update(overrides)
        return categories.BiliquidPropellant(**kwargs)
