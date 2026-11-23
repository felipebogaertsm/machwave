import dataclasses

import pytest

import machwave.models.feed_systems as feed_systems_models
import machwave.models.feed_systems.lines as line_models
import machwave.models.feed_systems.tank as tank_models
import machwave.models.propellants as propellants_models
import machwave.simulation.biliquid.states as biliquid_states
from tests.factories import (
    InjectorElementFactory,
    InjectorFactory,
    PropellantLineFactory,
    StackedTankPressureFedFeedSystemFactory,
    TankFactory,
)


RESISTANCE = feed_systems_models.FeedlineResistance(
    loss_coefficient=5.0, flow_area=2.0e-5
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
            oxidizer_line_resistance=RESISTANCE,
        )

        inlet = feed_system.get_inlet_states(line_states(feed_system))["oxidizer"]

        assert inlet.fluid_name == "N2O"
        assert inlet.pressure == pytest.approx(
            oxidizer_tank.get_pressure(
                oxidizer_mass, oxidizer_tank.initial_internal_energy
            )
        )
        assert inlet.temperature == pytest.approx(
            oxidizer_tank.get_temperature(
                oxidizer_mass, oxidizer_tank.initial_internal_energy
            )
        )
        assert inlet.density == pytest.approx(
            oxidizer_tank.get_density(
                oxidizer_mass, oxidizer_tank.initial_internal_energy
            )
        )

    def test_the_fuel_inlet_is_piston_pressurized_fuel(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build(piston_loss=2e5)
        oxidizer_tank = feed_system.lines["oxidizer"].tank
        fuel_tank = feed_system.lines["fuel"].tank
        oxidizer_mass = oxidizer_tank.initial_fluid_mass
        fuel_mass = fuel_tank.initial_fluid_mass

        inlet = feed_system.get_inlet_states(line_states(feed_system))["fuel"]

        assert inlet.fluid_name == fuel_tank.fluid_name
        assert inlet.pressure == pytest.approx(
            oxidizer_tank.get_pressure(
                oxidizer_mass, oxidizer_tank.initial_internal_energy
            )
            - 2e5
        )
        assert inlet.temperature == pytest.approx(
            fuel_tank.get_temperature(fuel_mass, fuel_tank.initial_internal_energy)
        )
        assert inlet.density == pytest.approx(
            fuel_tank.get_density(fuel_mass, fuel_tank.initial_internal_energy)
        )

    def test_a_third_line_is_pressurized_through_the_piston_too(self):
        feed_system = build_triliquid(piston_loss=2e5)
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        inlet = feed_system.get_inlet_states(line_states(feed_system))["diluent"]

        assert inlet.fluid_name == "Water"
        assert inlet.pressure == pytest.approx(
            oxidizer_tank.get_pressure(
                oxidizer_tank.initial_fluid_mass, oxidizer_tank.initial_internal_energy
            )
            - 2e5
        )

    def test_rejects_a_missing_line_state(self):
        feed_system = build_triliquid()
        states = line_states(feed_system)
        del states["diluent"]

        with pytest.raises(ValueError, match="diluent"):
            feed_system.get_inlet_states(states)


class TestFeedlineHeadPressure:
    """The cycle sets the feedline head pressure. The line loss depends on the flow."""

    def test_the_oxidizer_head_is_the_stack_pressure(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            oxidizer_line_resistance=RESISTANCE
        )
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        assert pressures["oxidizer"] == pytest.approx(
            oxidizer_tank.get_pressure(
                oxidizer_tank.initial_fluid_mass, oxidizer_tank.initial_internal_energy
            )
        )

    def test_the_fuel_head_is_the_stack_pressure_less_the_piston(self):
        piston_loss = 1e5
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            piston_loss=piston_loss,
            oxidizer_line_resistance=RESISTANCE,
            fuel_line_resistance=RESISTANCE,
        )
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        assert pressures["fuel"] == pytest.approx(
            oxidizer_tank.get_pressure(
                oxidizer_tank.initial_fluid_mass, oxidizer_tank.initial_internal_energy
            )
            - piston_loss
        )

    def test_the_piston_loss_holds_whatever_the_flow(self):
        """Seal friction is not a hydraulic loss. It is there at zero flow too."""
        feed_system = StackedTankPressureFedFeedSystemFactory.build(piston_loss=2e5)
        oxidizer_tank = feed_system.lines["oxidizer"].tank
        stack_pressure = oxidizer_tank.get_pressure(
            oxidizer_tank.initial_fluid_mass, oxidizer_tank.initial_internal_energy
        )

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        assert pressures["oxidizer"] - pressures["fuel"] == pytest.approx(2e5)
        assert pressures["oxidizer"] == pytest.approx(stack_pressure)


class TestInjectorSeesTheLineLoss:
    CHAMBER_PRESSURE = 20e5

    @staticmethod
    def solve(feed_system):
        injector = InjectorFactory.build(
            elements={
                "oxidizer": InjectorElementFactory.build(area=1.4e-5 / 0.48),
                "fuel": InjectorElementFactory.build(area=8.2e-6 / 0.48),
            }
        )
        inlet_states = feed_system.get_inlet_states(line_states(feed_system))
        flows = biliquid_states.get_injector_mass_flows(
            TestInjectorSeesTheLineLoss.CHAMBER_PRESSURE,
            injector=injector,
            lines=feed_system.lines,
            inlet_states=inlet_states,
            line_masses={name: 10.0 for name in feed_system.lines},
            is_feeding=True,
            d_t=1e-4,
        )
        return injector, inlet_states, flows

    def test_each_element_sees_the_head_less_its_own_line_loss(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build(
            piston_loss=1e5,
            oxidizer_line_resistance=RESISTANCE,
            fuel_line_resistance=feed_systems_models.FeedlineResistance(
                loss_coefficient=20.0, flow_area=2.0e-5
            ),
        )
        injector, inlet_states, flows = self.solve(feed_system)

        for name, line in feed_system.lines.items():
            head = inlet_states[name]
            seen = dataclasses.replace(
                head,
                pressure=head.pressure
                - line.resistance.get_pressure_drop(flows[name], head.density),
            )
            element = injector.elements[name]
            lossless_flow = element.get_mass_flow(
                inlet=head, chamber_pressure=self.CHAMBER_PRESSURE
            )
            # the element flow can miss by up to twice the solve tolerance
            assert flows[name] == pytest.approx(
                element.get_mass_flow(
                    inlet=seen, chamber_pressure=self.CHAMBER_PRESSURE
                ),
                abs=2.0 * biliquid_states.LINE_FLOW_RELATIVE_TOLERANCE * lossless_flow,
            )

    def test_one_line_resistance_leaves_the_other_line_alone(self):
        lossless = StackedTankPressureFedFeedSystemFactory.build(piston_loss=1e5)
        with_fuel_line = StackedTankPressureFedFeedSystemFactory.build(
            piston_loss=1e5, fuel_line_resistance=RESISTANCE
        )

        _, _, flows_lossless = self.solve(lossless)
        _, _, flows_with_line = self.solve(with_fuel_line)

        assert flows_with_line["oxidizer"] == flows_lossless["oxidizer"]
        assert 0.0 < flows_with_line["fuel"] < flows_lossless["fuel"]


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

    def test_rejects_a_negative_piston_loss(self):
        with pytest.raises(ValueError, match="piston_loss"):
            build_triliquid(piston_loss=-1.0)


class TestDeprecatedLineLosses:
    def test_fixed_line_losses_still_come_off_the_head_pressure(self):
        with pytest.warns(DeprecationWarning, match="fixed line losses"):
            feed_system = build_triliquid(piston_loss=2e5, line_losses={"diluent": 1e5})
        oxidizer_tank = feed_system.lines["oxidizer"].tank

        pressures = feed_system.get_inlet_pressures(line_states(feed_system))

        assert pressures["diluent"] == pytest.approx(
            oxidizer_tank.get_pressure(
                oxidizer_tank.initial_fluid_mass, oxidizer_tank.initial_internal_energy
            )
            - 2e5
            - 1e5
        )

    def test_the_two_line_constructor_still_carries_them(self):
        with pytest.warns(DeprecationWarning, match="fixed line losses"):
            feed_system = StackedTankPressureFedFeedSystemFactory.build(
                oxidizer_line_loss=3e5, fuel_line_loss=2e5
            )

        assert feed_system.line_losses == {"oxidizer": 3e5, "fuel": 2e5}

    def test_rejects_a_loss_keyed_by_an_unknown_line(self):
        with (
            pytest.warns(DeprecationWarning, match="fixed line losses"),
            pytest.raises(ValueError, match="coolant"),
        ):
            build_triliquid(line_losses={"coolant": 1e5})

    @pytest.mark.parametrize("line_name", ["oxidizer", "fuel"])
    def test_rejects_a_negative_line_loss(self, line_name):
        with (
            pytest.warns(DeprecationWarning, match="fixed line losses"),
            pytest.raises(ValueError, match=f"line_losses\\['{line_name}'\\]"),
        ):
            build_triliquid(line_losses={line_name: -1.0})


class TestInitialState:
    def test_the_line_state_starts_at_the_tank_loading(self):
        feed_system = StackedTankPressureFedFeedSystemFactory.build()

        state = feed_system.lines["fuel"].initial_state

        assert isinstance(state, line_models.LineState)
        assert state.fluid_mass == pytest.approx(
            feed_system.lines["fuel"].tank.initial_fluid_mass
        )
