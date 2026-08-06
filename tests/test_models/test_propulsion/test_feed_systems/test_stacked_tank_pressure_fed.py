import pytest

import machwave.models.feed_systems as feed_systems_models
import machwave.models.feed_systems.lines as line_models
import machwave.models.feed_systems.tank as tank_models
import machwave.models.propellants as propellants_models
from tests.factories import (
    PropellantLineFactory,
    StackedTankPressureFedFeedSystemFactory,
    TankFactory,
)


def line_states(feed_system):
    """The state of every line, as the tanks were loaded."""
    return {name: line.initial_state for name, line in feed_system.lines.items()}


def build_triliquid(**overrides):
    """A stack of an oxidizer over a fuel and a diluent, both below the piston."""
    lines = [
        PropellantLineFactory.build(
            name="oxidizer", role="oxidizer", tank=TankFactory.build(fluid_name="N2O")
        ),
        PropellantLineFactory.build(
            name="fuel",
            role="fuel",
            tank=TankFactory.build(fluid_name="Ethanol", initial_fluid_mass=3.0),
        ),
        PropellantLineFactory.build(
            name="diluent",
            role="additive",
            tank=TankFactory.build(fluid_name="Water", initial_fluid_mass=1.0),
        ),
    ]
    kwargs = dict(lines=lines, pressurizing_line="oxidizer")
    kwargs.update(overrides)
    return feed_systems_models.StackedTankPressureFedFeedSystem(**kwargs)


class TestInletStates:
    def test_every_line_gets_a_state_in_one_call(self):
        feed_system = build_triliquid()

        inlet_states = feed_system.get_inlet_states(line_states(feed_system))

        assert set(inlet_states) == {"oxidizer", "fuel", "diluent"}

    def test_the_oxidizer_inlet_reads_the_oxidizer_tank(self):
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

        inlet = feed_system.get_inlet_states(line_states(feed_system))["oxidizer"]

        assert inlet.fluid_name == "N2O"
        assert inlet.pressure == pytest.approx(
            oxidizer_tank.get_pressure(oxidizer_mass) - 3e5
        )
        assert inlet.temperature == pytest.approx(
            oxidizer_tank.get_temperature(oxidizer_mass)
        )
        assert inlet.density == pytest.approx(oxidizer_tank.get_density(oxidizer_mass))

    def test_the_fuel_inlet_is_piston_pressurized_fuel(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build(piston_loss=2e5)
        oxidizer_tank = feed_system.lines["oxidizer"].tank
        fuel_tank = feed_system.lines["fuel"].tank
        oxidizer_mass = oxidizer_tank.initial_fluid_mass
        fuel_mass = fuel_tank.initial_fluid_mass

        inlet = feed_system.get_inlet_states(line_states(feed_system))["fuel"]

        assert inlet.fluid_name == fuel_tank.fluid_name
        assert inlet.pressure == pytest.approx(
            oxidizer_tank.get_pressure(oxidizer_mass) - 2e5
        )
        assert inlet.temperature == pytest.approx(fuel_tank.get_temperature(fuel_mass))
        assert inlet.density == pytest.approx(fuel_tank.get_density(fuel_mass))

    def test_a_third_line_is_pressurized_through_the_piston_too(self):
        feed_system = build_triliquid(piston_loss=2e5, line_losses={"diluent": 1e5})
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        inlet = feed_system.get_inlet_states(line_states(feed_system))["diluent"]

        assert inlet.fluid_name == "Water"
        assert inlet.pressure == pytest.approx(
            oxidizer_tank.get_pressure(oxidizer_tank.initial_fluid_mass) - 2e5 - 1e5
        )

    def test_rejects_a_missing_line_state(self):
        feed_system = build_triliquid()
        states = line_states(feed_system)
        del states["diluent"]

        with pytest.raises(ValueError, match="diluent"):
            feed_system.get_inlet_states(states)


class TestFeedlineLoss:
    def test_no_line_leaves_the_tank_pressure_alone(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        assert pressures["oxidizer"] == oxidizer_tank.get_pressure(
            oxidizer_tank.initial_fluid_mass
        )

    def test_the_oxidizer_line_comes_off_the_oxidizer_side(self):
        oxidizer_line_loss = 3e5
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            oxidizer_line_loss=oxidizer_line_loss
        )
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        assert pressures["oxidizer"] == pytest.approx(
            oxidizer_tank.get_pressure(oxidizer_tank.initial_fluid_mass)
            - oxidizer_line_loss
        )

    def test_the_fuel_side_takes_the_piston_and_its_own_line(self):
        piston_loss = 1e5
        fuel_line_loss = 2e5
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            piston_loss=piston_loss,
            fuel_line_loss=fuel_line_loss,
            oxidizer_line_loss=3e5,
        )
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        # The oxidizer line is not on the fuel path.
        assert pressures["fuel"] == pytest.approx(
            oxidizer_tank.get_pressure(oxidizer_tank.initial_fluid_mass)
            - piston_loss
            - fuel_line_loss
        )

    def test_a_line_holds_the_inlet_pressure_below_the_lossless_one(self):
        with_line = StackedTankPressureFedFeedSystemFactory.build(fuel_line_loss=5e5)
        without_line = StackedTankPressureFedFeedSystemFactory.build()

        pressures = [
            feed_system.get_inlet_states(line_states(feed_system))["fuel"].pressure
            for feed_system in (with_line, without_line)
        ]

        assert 0.0 < pressures[0] < pressures[1]


class TestLines:
    def test_the_initial_propellant_mass_adds_up_every_line(self):
        feed_system = build_triliquid()

        assert feed_system.get_initial_propellant_mass() == pytest.approx(
            sum(line.tank.initial_fluid_mass for line in feed_system.lines.values())
        )

    def test_lines_are_found_by_role(self):
        feed_system = build_triliquid()

        oxidizer_lines = feed_system.get_lines_with_role(
            propellants_models.ComponentRole.OXIDIZER
        )
        additive_lines = feed_system.get_lines_with_role(
            propellants_models.ComponentRole.ADDITIVE
        )

        assert [line.name for line in oxidizer_lines] == ["oxidizer"]
        assert [line.name for line in additive_lines] == ["diluent"]

    def test_rejects_a_system_without_lines(self):
        with pytest.raises(ValueError, match="at least one"):
            feed_systems_models.StackedTankPressureFedFeedSystem(
                lines=[], pressurizing_line="oxidizer"
            )

    def test_rejects_two_lines_sharing_a_name(self):
        line = PropellantLineFactory.build(name="oxidizer")

        with pytest.raises(ValueError, match="unique"):
            feed_systems_models.StackedTankPressureFedFeedSystem(
                lines=[line, line], pressurizing_line="oxidizer"
            )


class TestValidation:
    def test_rejects_a_pressurizing_line_the_system_does_not_feed(self):
        with pytest.raises(ValueError, match="pressurizing_line"):
            build_triliquid(pressurizing_line="pressurant")

    def test_rejects_a_loss_keyed_by_an_unknown_line(self):
        with pytest.raises(ValueError, match="coolant"):
            build_triliquid(line_losses={"coolant": 1e5})

    def test_rejects_a_negative_piston_loss(self):
        with pytest.raises(ValueError, match="piston_loss"):
            build_triliquid(piston_loss=-1.0)

    @pytest.mark.parametrize("line_name", ["oxidizer", "fuel"])
    def test_rejects_a_negative_line_loss(self, line_name):
        with pytest.raises(ValueError, match=line_name):
            build_triliquid(line_losses={line_name: -1.0})


class TestInitialState:
    def test_the_line_state_starts_at_the_tank_loading(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()

        state = feed_system.lines["fuel"].initial_state

        assert isinstance(state, line_models.LineState)
        assert state.fluid_mass == pytest.approx(
            feed_system.lines["fuel"].tank.initial_fluid_mass
        )
