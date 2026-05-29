import pytest

import machwave.models.feed_systems.tank as tank_models
from machwave.models.thrust_chamber import MassFlowModel
from tests.factories import (
    BipropellantInjectorFactory,
    StackedTankPressureFedFeedSystemFactory,
)


def test_get_mass_flow_ox_delegates_to_injector_dispatch():
    """Feed-system call equals the injector's own dispatch on the ox tank."""
    oxidizer_mass = 5.0
    oxidizer_tank = tank_models.Tank(
        fluid_name="N2O",
        volume=0.01,
        temperature=293.0,
        initial_fluid_mass=oxidizer_mass,
    )
    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank=oxidizer_tank,
    )
    injector = BipropellantInjectorFactory.build(
        mass_flow_model_oxidizer=MassFlowModel.HEM,
    )
    chamber_pressure = 20e5

    actual = feed_system.get_mass_flow_ox(
        chamber_pressure, injector=injector, oxidizer_mass=oxidizer_mass
    )
    expected = injector.get_mass_flow_ox(
        tank=oxidizer_tank,
        pressure_upstream=feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass
        ),
        chamber_pressure=chamber_pressure,
        fluid_mass=oxidizer_mass,
    )
    assert actual == pytest.approx(expected)


def test_get_mass_flow_fuel_uses_piston_pressurized_upstream():
    """Fuel-side upstream is the oxidizer tank pressure minus piston loss."""
    feed_system = StackedTankPressureFedFeedSystemFactory.build(piston_loss=2e5)
    injector = BipropellantInjectorFactory.build()
    chamber_pressure = 15e5
    oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass
    fuel_mass = feed_system.fuel_tank.initial_fluid_mass

    actual = feed_system.get_mass_flow_fuel(
        chamber_pressure,
        injector=injector,
        fuel_mass=fuel_mass,
        oxidizer_mass=oxidizer_mass,
    )
    expected = injector.get_mass_flow_fuel(
        tank=feed_system.fuel_tank,
        pressure_upstream=feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass
        )
        - 2e5,
        chamber_pressure=chamber_pressure,
        fluid_mass=fuel_mass,
    )
    assert actual == pytest.approx(expected)
