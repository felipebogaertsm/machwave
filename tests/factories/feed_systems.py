from __future__ import annotations

from typing import Any

from machwave.models import feed_systems as feed_systems_models
from machwave.models.feed_systems import tanks


class TankFactory:
    @classmethod
    def build(cls, **overrides: Any) -> tanks.Tank:
        kwargs: dict[str, Any] = dict(
            fluid_name="N2O",
            volume=0.01,
            temperature=298.0,
            initial_fluid_mass=5.0,
        )
        kwargs.update(overrides)
        return tanks.Tank(**kwargs)


class StackedTankPressureFedFeedSystemFactory:
    @classmethod
    def build(
        cls, **overrides: Any
    ) -> feed_systems_models.StackedTankPressureFedFeedSystem:
        oxidizer_tank = overrides.pop("oxidizer_tank", None) or TankFactory.build(
            fluid_name="N2O", initial_fluid_mass=5.0
        )
        fuel_tank = overrides.pop("fuel_tank", None) or TankFactory.build(
            fluid_name="Ethanol", volume=0.008, initial_fluid_mass=3.0
        )
        kwargs: dict[str, Any] = dict(
            oxidizer_tank=oxidizer_tank,
            fuel_tank=fuel_tank,
            oxidizer_line_diameter=0.01,
            oxidizer_line_length=0.5,
            fuel_line_diameter=0.008,
            fuel_line_length=0.5,
        )
        kwargs.update(overrides)
        return feed_systems_models.StackedTankPressureFedFeedSystem(**kwargs)
