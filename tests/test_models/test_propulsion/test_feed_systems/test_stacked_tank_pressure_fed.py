import pytest

import machwave.models.feed_systems.tank as tank_models
from tests.factories import StackedTankPressureFedFeedSystemFactory


def test_oxidizer_inlet_state_reads_the_oxidizer_tank():
    """The oxidizer inlet carries the tank fluid at the tank state."""
    oxidizer_mass = 5.0
    oxidizer_tank = tank_models.Tank(
        fluid_name="N2O",
        volume=0.01,
        temperature=293.0,
        initial_fluid_mass=oxidizer_mass,
    )
    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank=oxidizer_tank,
        oxidizer_line_loss=3e5,
    )

    inlet = feed_system.get_oxidizer_inlet_state(oxidizer_mass=oxidizer_mass)

    assert inlet.fluid_name == "N2O"
    assert inlet.pressure == pytest.approx(
        feed_system.get_oxidizer_tank_pressure(oxidizer_mass=oxidizer_mass)
    )
    assert inlet.temperature == pytest.approx(
        oxidizer_tank.get_temperature(oxidizer_mass)
    )
    assert inlet.density == pytest.approx(oxidizer_tank.get_density(oxidizer_mass))


def test_fuel_inlet_state_is_piston_pressurized_fuel():
    """The fuel inlet carries fuel at the piston-pressurized upstream pressure."""
    feed_system = StackedTankPressureFedFeedSystemFactory.build(piston_loss=2e5)
    oxidizer_mass = feed_system.oxidizer_tank.initial_fluid_mass
    fuel_mass = feed_system.fuel_tank.initial_fluid_mass

    inlet = feed_system.get_fuel_inlet_state(
        oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass
    )

    assert inlet.fluid_name == feed_system.fuel_tank.fluid_name
    assert inlet.pressure == pytest.approx(
        feed_system.oxidizer_tank.get_pressure(oxidizer_mass) - 2e5
    )
    assert inlet.temperature == pytest.approx(
        feed_system.fuel_tank.get_temperature(fuel_mass)
    )
    assert inlet.density == pytest.approx(feed_system.fuel_tank.get_density(fuel_mass))


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

    def test_a_line_holds_the_inlet_pressure_below_the_lossless_one(self):
        with_line = StackedTankPressureFedFeedSystemFactory.build(fuel_line_loss=5e5)
        without_line = StackedTankPressureFedFeedSystemFactory.build()
        fuel_mass = with_line.fuel_tank.initial_fluid_mass
        oxidizer_mass = with_line.oxidizer_tank.initial_fluid_mass

        pressures = [
            feed_system.get_fuel_inlet_state(
                oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass
            ).pressure
            for feed_system in (with_line, without_line)
        ]

        assert 0.0 < pressures[0] < pressures[1]


class TestValidation:
    @pytest.mark.parametrize(
        "field",
        ["piston_loss", "oxidizer_line_loss", "fuel_line_loss"],
    )
    def test_rejects_a_negative_pressure_loss(self, field):
        with pytest.raises(ValueError, match=field):
            StackedTankPressureFedFeedSystemFactory.build(**{field: -1.0})
