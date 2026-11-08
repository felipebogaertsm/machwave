import dataclasses
import math

import numpy as np
import pytest

import machwave.models.feed_systems.lines as line_models
import machwave.models.propellants as propellants_models
from tests.factories import PropellantLineFactory, TankFactory, TankPlacementFactory

TANK_VOLUME = 0.01
TANK_INNER_RADIUS = 0.1
TANK_LENGTH = TANK_VOLUME / (math.pi * TANK_INNER_RADIUS**2)
TANK_AFT_END = 0.3


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

    def test_has_no_tank_placement_by_default(self):
        assert PropellantLineFactory.build().tank_placement is None

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


class TestTankPlacement:
    def test_the_tank_length_follows_from_its_volume(self):
        placement = TankPlacementFactory.build(inner_diameter=0.2)

        assert placement.get_length(0.01) == pytest.approx(0.01 / (math.pi * 0.1**2))

    def test_a_tank_at_the_nozzle_exit_is_valid(self):
        placement = TankPlacementFactory.build(nozzle_exit_to_aft_end_distance=0.0)

        assert placement.nozzle_exit_to_aft_end_distance == 0.0

    @pytest.mark.parametrize("inner_diameter", [0.0, -0.1])
    def test_rejects_a_non_positive_inner_diameter(self, inner_diameter):
        with pytest.raises(ValueError, match="inner_diameter"):
            TankPlacementFactory.build(inner_diameter=inner_diameter)

    def test_rejects_a_negative_nozzle_exit_to_aft_end_distance(self):
        with pytest.raises(ValueError, match="nozzle_exit_to_aft_end_distance"):
            TankPlacementFactory.build(nozzle_exit_to_aft_end_distance=-0.1)


def build_placed_line(**tank_overrides):
    tank = TankFactory.build(volume=TANK_VOLUME, **tank_overrides)
    return PropellantLineFactory.build(
        tank=tank,
        tank_placement=TankPlacementFactory.build(
            inner_diameter=2 * TANK_INNER_RADIUS,
            nozzle_exit_to_aft_end_distance=TANK_AFT_END,
        ),
    )


class TestPropellantLineMassProperties:
    @pytest.mark.parametrize(
        "fill", ["saturated_liquid", "overfilled_liquid", "vapor_only"]
    )
    def test_a_single_phase_fills_the_tank_as_a_uniform_cylinder(self, fill):
        line = build_placed_line()
        tank = line.tank
        fluid_mass = {
            "saturated_liquid": tank.saturated_liquid_density * TANK_VOLUME,
            "overfilled_liquid": 1.005 * tank.saturated_liquid_density * TANK_VOLUME,
            "vapor_only": 0.5 * tank.saturated_vapor_density * TANK_VOLUME,
        }[fill]

        cog, moi = line.get_mass_properties(
            line_models.LineState(fluid_mass=fluid_mass)
        )

        transverse = fluid_mass * (TANK_INNER_RADIUS**2 / 4 + TANK_LENGTH**2 / 12)
        np.testing.assert_allclose(cog, [TANK_AFT_END + TANK_LENGTH / 2, 0.0, 0.0])
        np.testing.assert_allclose(
            moi,
            np.diag([fluid_mass * TANK_INNER_RADIUS**2 / 2, transverse, transverse]),
        )

    def test_liquid_settled_over_half_the_tank_under_vapor(self):
        line = build_placed_line()
        liquid_density = line.tank.saturated_liquid_density
        vapor_density = line.tank.saturated_vapor_density
        liquid_mass = liquid_density * TANK_VOLUME / 2
        vapor_mass = vapor_density * TANK_VOLUME / 2

        cog, moi = line.get_mass_properties(
            line_models.LineState(fluid_mass=liquid_mass + vapor_mass)
        )

        liquid_position = TANK_AFT_END + TANK_LENGTH / 4
        vapor_position = TANK_AFT_END + 3 * TANK_LENGTH / 4
        expected_position = (
            liquid_mass * liquid_position + vapor_mass * vapor_position
        ) / (liquid_mass + vapor_mass)
        phase_transverse_moment_per_mass = (
            TANK_INNER_RADIUS**2 / 4 + (TANK_LENGTH / 2) ** 2 / 12
        )
        transverse = (
            (liquid_mass + vapor_mass) * phase_transverse_moment_per_mass
            + liquid_mass * (liquid_position - expected_position) ** 2
            + vapor_mass * (vapor_position - expected_position) ** 2
        )
        np.testing.assert_allclose(cog, [expected_position, 0.0, 0.0])
        np.testing.assert_allclose(
            moi,
            np.diag(
                [
                    (liquid_mass + vapor_mass) * TANK_INNER_RADIUS**2 / 2,
                    transverse,
                    transverse,
                ]
            ),
        )

    def test_an_empty_tank_has_no_center_of_gravity_and_no_inertia(self):
        cog, moi = build_placed_line().get_mass_properties(
            line_models.LineState(fluid_mass=0.0)
        )

        assert np.isnan(cog).all()
        np.testing.assert_array_equal(moi, np.zeros((3, 3)))

    def test_a_tank_running_an_energy_balance_matches_at_its_loaded_state(self):
        energy_balance_line = build_placed_line(isothermal=False)
        isothermal_line = build_placed_line(isothermal=True)

        energy_balance_cog, energy_balance_moi = (
            energy_balance_line.get_mass_properties(energy_balance_line.initial_state)
        )
        isothermal_cog, isothermal_moi = isothermal_line.get_mass_properties(
            isothermal_line.initial_state
        )

        np.testing.assert_allclose(energy_balance_cog, isothermal_cog)
        np.testing.assert_allclose(energy_balance_moi, isothermal_moi)

    def test_rejects_a_line_without_a_tank_placement(self):
        line = PropellantLineFactory.build()

        with pytest.raises(ValueError, match="tank_placement"):
            line.get_mass_properties(line.initial_state)
