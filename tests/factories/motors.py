from __future__ import annotations

from typing import Any

import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.propellants.formulations.solid as solid_propellants

from tests.factories.feed_systems import StackedTankPressureFedFeedSystemFactory
from tests.factories.grain import BatesSegmentFactory
from tests.factories.propellants import BiliquidPropellantFactory
from tests.factories.thrust_chamber import (
    BiliquidEngineThrustChamberFactory,
    SolidMotorThrustChamberFactory,
)


class SolidMotorFactory:
    """Defaults to a single-segment BATES motor with KNDX propellant."""

    @classmethod
    def build(cls, **overrides: Any) -> motors_models.SolidMotor:
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
        return motors_models.SolidMotor(**kwargs)


class BiliquidEngineFactory:
    """Defaults to an N2O/Ethanol engine on a pressure-fed feed system."""

    @classmethod
    def build(cls, **overrides: Any) -> motors_models.BiliquidEngine:
        propellant = (
            overrides.pop("propellant", None) or BiliquidPropellantFactory.build()
        )
        thrust_chamber = (
            overrides.pop("thrust_chamber", None)
            or BiliquidEngineThrustChamberFactory.build()
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
        return motors_models.BiliquidEngine(**kwargs)
