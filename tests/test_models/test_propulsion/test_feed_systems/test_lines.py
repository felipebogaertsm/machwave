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
