import pytest

import machwave.models.feed_systems as feed_systems_models
import machwave.models.propellants as propellants_models
import machwave.simulation.biliquid.states as biliquid_states
from machwave.models.feed_systems.lines import LineState
from tests.factories import (
    InjectorElementFactory,
    InjectorFactory,
    PropellantLineFactory,
    SingleLinePressureFedFeedSystemFactory,
    TankFactory,
)


def line_states(feed_system):
    return {name: line.initial_state for name, line in feed_system.lines.items()}


class TestInletState:
    def test_the_inlet_reads_the_tank(self):
        tank = TankFactory.build(fluid_name="N2O", initial_fluid_mass=5.0)
        feed_system = SingleLinePressureFedFeedSystemFactory.build(
            line=PropellantLineFactory.build(tank=tank)
        )

        inlet = feed_system.get_inlet_states(line_states(feed_system))["oxidizer"]

        assert inlet.fluid_name == "N2O"
        assert inlet.pressure == pytest.approx(tank.get_pressure(5.0))
        assert inlet.temperature == pytest.approx(tank.get_temperature(5.0))
        assert inlet.density == pytest.approx(tank.get_density(5.0))

    def test_the_feedline_comes_off_the_tank_pressure(self):
        feed_system = SingleLinePressureFedFeedSystemFactory.build(line_loss=3e5)
        tank = feed_system.line.tank

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        assert pressures["oxidizer"] == pytest.approx(
            tank.get_pressure(tank.initial_fluid_mass) - 3e5
        )

    def test_an_empty_tank_delivers_no_pressure(self):
        feed_system = SingleLinePressureFedFeedSystemFactory.build()

        pressures = feed_system.get_inlet_pressures(
            {"oxidizer": LineState(fluid_mass=0.0)}
        )

        assert pressures["oxidizer"] == 0.0

    def test_the_tank_blows_down_as_it_drains(self):
        feed_system = SingleLinePressureFedFeedSystemFactory.build(
            line=PropellantLineFactory.build(
                tank=TankFactory.build(fluid_name="N2O", initial_fluid_mass=5.0)
            )
        )

        pressures = [
            feed_system.get_inlet_pressures({"oxidizer": LineState(fluid_mass=mass)})[
                "oxidizer"
            ]
            for mass in (5.0, 0.5, 0.05)
        ]

        assert pressures[0] >= pressures[1] > pressures[2]


class TestSingleLineContract:
    def test_the_system_feeds_exactly_one_line(self):
        feed_system = SingleLinePressureFedFeedSystemFactory.build()

        assert list(feed_system.lines) == ["oxidizer"]
        assert feed_system.line is feed_system.lines["oxidizer"]

    def test_the_initial_propellant_mass_is_the_one_tank_loading(self):
        feed_system = SingleLinePressureFedFeedSystemFactory.build()

        assert feed_system.get_initial_propellant_mass() == pytest.approx(
            feed_system.line.tank.initial_fluid_mass
        )

    def test_a_monoliquid_line_carries_the_fuel_role(self):
        feed_system = SingleLinePressureFedFeedSystemFactory.build(
            line=PropellantLineFactory.build(name="propellant", role="fuel")
        )

        assert feed_system.get_lines_with_role(
            propellants_models.ComponentRole.FUEL
        ) == (feed_system.line,)
        assert (
            feed_system.get_lines_with_role(propellants_models.ComponentRole.OXIDIZER)
            == ()
        )

    def test_one_line_feeds_one_injector_element(self):
        """The simulation-facing flow helper holds below two lines."""
        feed_system = SingleLinePressureFedFeedSystemFactory.build()
        injector = InjectorFactory.build(
            elements={"oxidizer": InjectorElementFactory.build()}
        )

        flows = biliquid_states.get_injector_mass_flows(
            20e5,
            injector=injector,
            inlet_states=feed_system.get_inlet_states(line_states(feed_system)),
            line_masses={"oxidizer": feed_system.line.tank.initial_fluid_mass},
            is_feeding=True,
            d_t=1e-4,
        )

        assert list(flows) == ["oxidizer"]
        assert flows["oxidizer"] > 0.0


class TestOxidizerTankConstructor:
    def test_names_the_line_oxidizer(self):
        feed_system = (
            feed_systems_models.SingleLinePressureFedFeedSystem.from_oxidizer_tank(
                oxidizer_tank=TankFactory.build()
            )
        )

        assert feed_system.line.name == "oxidizer"
        assert feed_system.line.role is propellants_models.ComponentRole.OXIDIZER

    def test_carries_the_feedline_loss(self):
        feed_system = (
            feed_systems_models.SingleLinePressureFedFeedSystem.from_oxidizer_tank(
                oxidizer_tank=TankFactory.build(), line_loss=2e5
            )
        )

        assert feed_system.line_loss == 2e5


class TestValidation:
    def test_rejects_a_negative_line_loss(self):
        with pytest.raises(ValueError, match="line_loss"):
            SingleLinePressureFedFeedSystemFactory.build(line_loss=-1.0)
