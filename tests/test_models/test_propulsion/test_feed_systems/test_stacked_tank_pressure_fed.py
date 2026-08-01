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
        pressure_upstream=feed_system.oxidizer_tank.get_pressure(oxidizer_mass) - 2e5,
        chamber_pressure=chamber_pressure,
        fluid_mass=fuel_mass,
    )
    assert actual == pytest.approx(expected)


class TestFeedlineLoss:
    def test_no_line_leaves_the_tank_pressure_alone(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass

        assert feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass
        ) == feed_system.oxidizer_tank.get_pressure(oxidizer_mass)

    def test_the_oxidizer_line_comes_off_the_oxidizer_side(self):
        oxidizer_line_loss = 3e5
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            oxidizer_line_loss=oxidizer_line_loss
        )
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass

        assert feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass
        ) == pytest.approx(
            feed_system.oxidizer_tank.get_pressure(oxidizer_mass) - oxidizer_line_loss
        )

    def test_the_fuel_side_takes_the_piston_and_its_own_line(self):
        piston_loss = 1e5
        fuel_line_loss = 2e5
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            piston_loss=piston_loss,
            fuel_line_loss=fuel_line_loss,
            oxidizer_line_loss=3e5,
        )
        oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass
        fuel_mass = feed_system.fuel_tank.initial_fluid_mass

        # The oxidizer line is not on the fuel path.
        assert feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass
        ) == pytest.approx(
            feed_system.oxidizer_tank.get_pressure(oxidizer_mass)
            - piston_loss
            - fuel_line_loss
        )

    def test_a_line_holds_the_flow_below_the_lossless_one(self):
        with_line = StackedTankPressureFedFeedSystemFactory.build(fuel_line_loss=5e5)
        without_line = StackedTankPressureFedFeedSystemFactory.build()
        injector = BipropellantInjectorFactory.build()
        chamber_pressure = 15e5
        fuel_mass = with_line.fuel_tank.initial_fluid_mass
        oxidizer_mass = with_line.oxidizer_tank.initial_fluid_mass

        flows = [
            feed_system.get_mass_flow_fuel(
                chamber_pressure,
                injector=injector,
                fuel_mass=fuel_mass,
                oxidizer_mass=oxidizer_mass,
            )
            for feed_system in (with_line, without_line)
        ]

        assert 0.0 < flows[0] < flows[1]


class TestValidation:
    @pytest.mark.parametrize(
        "field",
        ["piston_loss", "oxidizer_line_loss", "fuel_line_loss"],
    )
    def test_rejects_a_negative_pressure_loss(self, field):
        with pytest.raises(ValueError, match=field):
            StackedTankPressureFedFeedSystemFactory.build(**{field: -1.0})
