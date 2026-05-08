"""Factories for motor model instances (SolidMotor, LiquidEngine).

These compose grain, propellant, thrust-chamber, and feed-system factories so a
test only needs to override the layers it cares about.
"""

from __future__ import annotations

from typing import Any

from machwave.models import grain as grain_models
from machwave.models import motors
from machwave.models.propellants.formulations import solid as solid_propellants

from tests.factories.feed_systems import StackedTankPressureFedFeedSystemFactory
from tests.factories.grain import BatesSegmentFactory
from tests.factories.propellants import BiliquidPropellantFactory
from tests.factories.thrust_chamber import (
    LiquidEngineThrustChamberFactory,
    SolidMotorThrustChamberFactory,
)


class SolidMotorFactory:
    """A small single-segment BATES SolidMotor with KNDX propellant."""

    @classmethod
    def build(cls, **overrides: Any) -> motors.SolidMotor:
        grain = overrides.pop("grain", None)
        if grain is None:
            grain = grain_models.Grain()
            grain.add_segment(BatesSegmentFactory.build())

        propellant = overrides.pop("propellant", None) or solid_propellants.KNDX
        thrust_chamber = (
            overrides.pop("thrust_chamber", None)
            or SolidMotorThrustChamberFactory.build()
        )

        kwargs: dict[str, Any] = dict(
            grain=grain,
            propellant=propellant,
            thrust_chamber=thrust_chamber,
        )
        kwargs.update(overrides)
        return motors.SolidMotor(**kwargs)


class LiquidEngineFactory:
    """A small N2O/Ethanol LiquidEngine wired to a pressure-fed feed system."""

    @classmethod
    def build(cls, **overrides: Any) -> motors.LiquidEngine:
        propellant = (
            overrides.pop("propellant", None) or BiliquidPropellantFactory.build()
        )
        thrust_chamber = (
            overrides.pop("thrust_chamber", None)
            or LiquidEngineThrustChamberFactory.build()
        )
        feed_system = (
            overrides.pop("feed_system", None)
            or StackedTankPressureFedFeedSystemFactory.build()
        )

        kwargs: dict[str, Any] = dict(
            propellant=propellant,
            thrust_chamber=thrust_chamber,
            feed_system=feed_system,
            oxidizer_tank_cog=0.5,
            fuel_tank_cog=0.4,
        )
        kwargs.update(overrides)
        return motors.LiquidEngine(**kwargs)
