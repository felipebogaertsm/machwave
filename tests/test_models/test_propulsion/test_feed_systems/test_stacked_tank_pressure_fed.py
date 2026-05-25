import pytest

import machwave.models.feed_systems.tanks as tanks
from machwave.models.thrust_chamber import MassFlowModel
from tests.factories import (
    BipropellantInjectorFactory,
    StackedTankPressureFedFeedSystemFactory,
)


def test_get_mass_flow_ox_delegates_to_injector_dispatch():
    """Feed-system call equals the injector's own dispatch on the ox tank."""
    oxidizer_tank = tanks.Tank(
        fluid_name="N2O", volume=0.01, temperature=293.0, initial_fluid_mass=5.0
    )
    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank=oxidizer_tank,
    )
    injector = BipropellantInjectorFactory.build(
        mass_flow_model_oxidizer=MassFlowModel.HEM,
    )
    chamber_pressure = 20e5

    actual = feed_system.get_mass_flow_ox(chamber_pressure, injector=injector)
    expected = injector.get_mass_flow_ox(
        tank=oxidizer_tank,
        pressure_upstream=feed_system.get_oxidizer_tank_pressure(),
        chamber_pressure=chamber_pressure,
    )
    assert actual == pytest.approx(expected)


def test_get_mass_flow_fuel_uses_piston_pressurized_upstream():
    """Fuel-side upstream is the oxidizer tank pressure minus piston loss."""
    feed_system = StackedTankPressureFedFeedSystemFactory.build(piston_loss=2e5)
    injector = BipropellantInjectorFactory.build()
    chamber_pressure = 15e5

    actual = feed_system.get_mass_flow_fuel(chamber_pressure, injector=injector)
    expected = injector.get_mass_flow_fuel(
        tank=feed_system.fuel_tank,
        pressure_upstream=feed_system.get_oxidizer_tank_pressure() - 2e5,
        chamber_pressure=chamber_pressure,
    )
    assert actual == pytest.approx(expected)
