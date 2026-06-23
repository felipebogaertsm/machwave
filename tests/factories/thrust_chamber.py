from __future__ import annotations

from typing import Any

import machwave.common.mass_properties as mass_properties
import machwave.models.thrust_chamber as thrust_chamber_models

_DRY_MASS_PROPERTIES_SENTINEL = object()


def _resolve_dry_mass_properties(
    overrides: dict[str, Any], **defaults: Any
) -> mass_properties.DryMassProperties | None:
    """
    Build a DryMassProperties from flat factory overrides.

    Passing `dry_mass_properties` (including None) takes precedence; otherwise
    the flat `dry_mass`/`center_of_gravity_coordinate`/`moment_of_inertia`
    overrides are merged onto the defaults.
    """
    explicit = overrides.pop("dry_mass_properties", _DRY_MASS_PROPERTIES_SENTINEL)
    if explicit is not _DRY_MASS_PROPERTIES_SENTINEL:
        return explicit

    return mass_properties.DryMassProperties(
        dry_mass=overrides.pop("dry_mass", defaults["dry_mass"]),
        center_of_gravity_coordinate=overrides.pop(
            "center_of_gravity_coordinate", defaults["center_of_gravity_coordinate"]
        ),
        moment_of_inertia=overrides.pop(
            "moment_of_inertia", defaults["moment_of_inertia"]
        ),
    )


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
        dry_mass_properties = _resolve_dry_mass_properties(
            overrides,
            dry_mass=0.85,
            center_of_gravity_coordinate=(0.04, 0.0, 0.0),
            moment_of_inertia=(0.02, 0.02, 0.005),
        )
        kwargs: dict[str, Any] = dict(
            nozzle=nozzle,
            combustion_chamber=combustion_chamber,
            nozzle_exit_to_grain_port_distance=0.01,
            dry_mass_properties=dry_mass_properties,
        )
        kwargs.update(overrides)
        return thrust_chamber_models.SolidMotorThrustChamber(**kwargs)


class BiliquidEngineThrustChamberFactory:
    @classmethod
    def build(
        cls, **overrides: Any
    ) -> thrust_chamber_models.BiliquidEngineThrustChamber:
        nozzle = overrides.pop("nozzle", None) or NozzleFactory.build()
        injector = (
            overrides.pop("injector", None) or BipropellantInjectorFactory.build()
        )
        combustion_chamber = (
            overrides.pop("combustion_chamber", None)
            or CombustionChamberFactory.build()
        )
        dry_mass_properties = _resolve_dry_mass_properties(
            overrides,
            dry_mass=2.0,
            center_of_gravity_coordinate=(0.02, 0.0, 0.0),
            moment_of_inertia=(0.05, 0.05, 0.01),
        )
        kwargs: dict[str, Any] = dict(
            nozzle=nozzle,
            injector=injector,
            combustion_chamber=combustion_chamber,
            dry_mass_properties=dry_mass_properties,
        )
        kwargs.update(overrides)
        return thrust_chamber_models.BiliquidEngineThrustChamber(**kwargs)
