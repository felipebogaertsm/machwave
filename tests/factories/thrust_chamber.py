from __future__ import annotations

from typing import Any

import machwave.models.thrust_chamber as thrust_chamber_models


class NozzleFactory:
    @classmethod
    def build(cls, **overrides: Any) -> thrust_chamber_models.Nozzle:
        kwargs: dict[str, Any] = dict(
            inlet_diameter=50.8e-3,
            throat_diameter=25.4e-3,
            divergent_angle=15,
            convergent_angle=45,
            expansion_ratio=4,
        )
        kwargs.update(overrides)
        return thrust_chamber_models.Nozzle(**kwargs)


class CombustionChamberFactory:
    @classmethod
    def build(cls, **overrides: Any) -> thrust_chamber_models.CombustionChamber:
        kwargs: dict[str, Any] = dict(
            casing_inner_diameter=70e-3,
            casing_outer_diameter=80e-3,
            internal_length=0.3,
            thermal_liner_thickness=2e-3,
        )
        kwargs.update(overrides)
        return thrust_chamber_models.CombustionChamber(**kwargs)


class BipropellantInjectorFactory:
    @classmethod
    def build(cls, **overrides: Any) -> thrust_chamber_models.BipropellantInjector:
        kwargs: dict[str, Any] = dict(
            discharge_coefficient_fuel=0.48,
            discharge_coefficient_oxidizer=0.48,
            area_fuel=8.2e-6 / 0.48,
            area_ox=1.4e-5 / 0.48,
        )
        kwargs.update(overrides)
        return thrust_chamber_models.BipropellantInjector(**kwargs)


class SolidMotorThrustChamberFactory:
    @classmethod
    def build(cls, **overrides: Any) -> thrust_chamber_models.SolidMotorThrustChamber:
        nozzle = overrides.pop("nozzle", None) or NozzleFactory.build()
        combustion_chamber = (
            overrides.pop("combustion_chamber", None)
            or CombustionChamberFactory.build()
        )
        kwargs: dict[str, Any] = dict(
            nozzle=nozzle,
            combustion_chamber=combustion_chamber,
            dry_mass=0.85,
            nozzle_exit_to_grain_port_distance=0.01,
            center_of_gravity_coordinate=(0.04, 0.0, 0.0),
        )
        kwargs.update(overrides)
        return thrust_chamber_models.SolidMotorThrustChamber(**kwargs)


class LiquidEngineThrustChamberFactory:
    @classmethod
    def build(cls, **overrides: Any) -> thrust_chamber_models.LiquidEngineThrustChamber:
        nozzle = overrides.pop("nozzle", None) or NozzleFactory.build()
        injector = (
            overrides.pop("injector", None) or BipropellantInjectorFactory.build()
        )
        combustion_chamber = (
            overrides.pop("combustion_chamber", None)
            or CombustionChamberFactory.build()
        )
        kwargs: dict[str, Any] = dict(
            nozzle=nozzle,
            injector=injector,
            combustion_chamber=combustion_chamber,
            dry_mass=2.0,
            center_of_gravity_coordinate=(0.02, 0.0, 0.0),
        )
        kwargs.update(overrides)
        return thrust_chamber_models.LiquidEngineThrustChamber(**kwargs)
