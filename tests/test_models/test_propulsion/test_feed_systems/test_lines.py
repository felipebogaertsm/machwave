import dataclasses

import pytest

import machwave.models.feed_systems.lines as line_models
import machwave.models.propellants as propellants_models
from tests.factories import PropellantLineFactory, TankFactory


class TestPropellantLine:
    def test_carries_a_name_a_role_and_a_tank(self):
        tank = TankFactory.build()
        line = PropellantLineFactory.build(name="oxidizer", tank=tank)

        assert line.name == "oxidizer"
        assert line.role is propellants_models.ComponentRole.OXIDIZER
        assert line.tank is tank

    def test_coerces_the_role_from_its_value(self):
        line = PropellantLineFactory.build(role="fuel")

        assert line.role is propellants_models.ComponentRole.FUEL

    def test_an_additive_line_is_a_valid_role(self):
        line = PropellantLineFactory.build(name="diluent", role="additive")

        assert line.role is propellants_models.ComponentRole.ADDITIVE

    def test_rejects_an_empty_name(self):
        with pytest.raises(ValueError, match="name"):
            PropellantLineFactory.build(name="")

    def test_rejects_an_unknown_role(self):
        with pytest.raises(ValueError, match="pressurant"):
            PropellantLineFactory.build(role="pressurant")

    def test_is_frozen(self):
        line = PropellantLineFactory.build()

        with pytest.raises(dataclasses.FrozenInstanceError):
            line.name = "fuel"


class TestPropellantLineInitialState:
    def test_starts_at_the_tank_loading(self):
        tank = TankFactory.build(initial_fluid_mass=4.0)
        line = PropellantLineFactory.build(tank=tank)

        assert line.initial_state.fluid_mass == pytest.approx(4.0)

    def test_an_isothermal_tank_carries_no_internal_energy(self):
        line = PropellantLineFactory.build(tank=TankFactory.build(isothermal=True))

        assert line.initial_state.internal_energy is None

    def test_a_tank_running_an_energy_balance_starts_at_its_loaded_energy(self):
        tank = TankFactory.build(isothermal=False)
        line = PropellantLineFactory.build(tank=tank)

        assert line.initial_state.internal_energy == pytest.approx(
            tank.initial_internal_energy
        )


class TestLineState:
    def test_defaults_to_no_internal_energy(self):
        state = line_models.LineState(fluid_mass=1.0)

        assert state.fluid_mass == pytest.approx(1.0)
        assert state.internal_energy is None

    def test_an_empty_line_is_a_valid_state(self):
        assert line_models.LineState(fluid_mass=0.0).fluid_mass == 0.0

    def test_rejects_a_negative_fluid_mass(self):
        with pytest.raises(ValueError, match="fluid_mass"):
            line_models.LineState(fluid_mass=-1.0)


class TestFeedlineResistance:
    def test_drops_k_times_the_dynamic_pressure(self):
        """dP = K rho v^2 / 2, with v = mdot / (rho A)."""
        resistance = line_models.FeedlineResistance(
            loss_coefficient=4.0, flow_area=1.0e-4
        )
        mass_flow, density = 0.8, 800.0
        velocity = mass_flow / (density * 1.0e-4)

        assert resistance.get_pressure_drop(mass_flow, density) == pytest.approx(
            4.0 * 0.5 * density * velocity**2
        )

    def test_drops_nothing_at_zero_flow(self):
        resistance = line_models.FeedlineResistance(
            loss_coefficient=4.0, flow_area=1.0e-4
        )

        assert resistance.get_pressure_drop(0.0, 800.0) == 0.0

    @pytest.mark.parametrize("ratio", [0.25, 0.5, 2.0])
    def test_scales_with_the_square_of_the_flow(self, ratio):
        resistance = line_models.FeedlineResistance(
            loss_coefficient=4.0, flow_area=1.0e-4
        )

        assert resistance.get_pressure_drop(ratio * 0.8, 800.0) == pytest.approx(
            ratio**2 * resistance.get_pressure_drop(0.8, 800.0)
        )

    def test_scales_inversely_with_density(self):
        resistance = line_models.FeedlineResistance(
            loss_coefficient=4.0, flow_area=1.0e-4
        )

        assert resistance.get_pressure_drop(0.8, 400.0) == pytest.approx(
            2.0 * resistance.get_pressure_drop(0.8, 800.0)
        )

    def test_the_design_point_drops_what_it_was_built_for(self):
        resistance = line_models.FeedlineResistance.from_design_point(
            pressure_drop=2e5, mass_flow=0.83, density=725.0, flow_area=9.37e-5
        )

        assert resistance.get_pressure_drop(0.83, 725.0) == pytest.approx(2e5)
        assert resistance.flow_area == 9.37e-5

    def test_a_line_without_resistance_drops_nothing(self):
        line = PropellantLineFactory.build()

        assert line.resistance is None
        assert line.get_pressure_drop(0.8, 800.0) == 0.0

    def test_a_line_takes_its_resistance_drop(self):
        resistance = line_models.FeedlineResistance(
            loss_coefficient=4.0, flow_area=1.0e-4
        )
        line = PropellantLineFactory.build(resistance=resistance)

        assert line.get_pressure_drop(0.8, 800.0) == resistance.get_pressure_drop(
            0.8, 800.0
        )

    @pytest.mark.parametrize(
        "kwargs, match",
        [
            (dict(loss_coefficient=-1.0, flow_area=1.0e-4), "loss_coefficient"),
            (dict(loss_coefficient=1.0, flow_area=0.0), "flow_area"),
        ],
    )
    def test_rejects_invalid_parameters(self, kwargs, match):
        with pytest.raises(ValueError, match=match):
            line_models.FeedlineResistance(**kwargs)

    @pytest.mark.parametrize(
        "overrides, match",
        [
            (dict(pressure_drop=-1.0), "pressure_drop"),
            (dict(mass_flow=0.0), "mass_flow"),
            (dict(density=0.0), "density"),
        ],
    )
    def test_rejects_an_invalid_design_point(self, overrides, match):
        kwargs = dict(
            pressure_drop=2e5, mass_flow=0.83, density=725.0, flow_area=9.37e-5
        )
        kwargs.update(overrides)

        with pytest.raises(ValueError, match=match):
            line_models.FeedlineResistance.from_design_point(**kwargs)

    def test_rejects_a_negative_flow(self):
        resistance = line_models.FeedlineResistance(
            loss_coefficient=4.0, flow_area=1.0e-4
        )

        with pytest.raises(ValueError, match="mass_flow"):
            resistance.get_pressure_drop(-0.1, 800.0)
