"""A tank running an energy balance cools as it drains.

An isothermal tank holds its saturation pressure flat for as long as any
liquid remains, which a self-pressurizing tank does not do: the fluid left
behind boils to refill the ullage and cools doing it. The energy balance
carries the tank's internal energy alongside its mass and takes out the
enthalpy of whatever leaves.
"""

import CoolProp.CoolProp as CP
import pytest

import machwave.models.feed_systems.tank as tank_models

FLUID = "N2O"
VOLUME = 0.01
TEMPERATURE = 293.0
FLUID_MASS = 5.0


def build(isothermal, **overrides):
    arguments = dict(
        fluid_name=FLUID,
        volume=VOLUME,
        temperature=TEMPERATURE,
        initial_fluid_mass=FLUID_MASS,
        isothermal=isothermal,
    )
    arguments.update(overrides)
    return tank_models.Tank(**arguments)


def drain(tank, mass_drained, fluid_mass=FLUID_MASS, internal_energy=None):
    """Take one lump of fluid out, with the enthalpy it carries."""
    if internal_energy is None:
        internal_energy = tank.initial_internal_energy
    outflow_enthalpy = tank.get_outflow_specific_enthalpy(fluid_mass, internal_energy)
    return (
        fluid_mass - mass_drained,
        internal_energy - mass_drained * outflow_enthalpy,
    )


class TestInitialInternalEnergy:
    def test_matches_the_loaded_state(self):
        tank = build(isothermal=False)

        assert tank.initial_internal_energy == pytest.approx(
            FLUID_MASS
            * CP.PropsSI("U", "T", TEMPERATURE, "D", FLUID_MASS / VOLUME, FLUID)
        )

    def test_an_empty_tank_carries_none(self):
        tank = build(isothermal=False, initial_fluid_mass=0.0)

        assert tank.initial_internal_energy == 0.0


class TestIsothermalTankIgnoresIt:
    def test_temperature_holds(self):
        tank = build(isothermal=True)

        assert tank.get_temperature(FLUID_MASS) == TEMPERATURE
        assert tank.get_temperature(FLUID_MASS, 1.0) == TEMPERATURE

    def test_pressure_holds(self):
        tank = build(isothermal=True)

        assert tank.get_pressure(FLUID_MASS, 1.0) == tank.get_pressure(FLUID_MASS)

    def test_it_needs_no_internal_energy(self):
        tank = build(isothermal=True)

        assert tank.get_pressure(FLUID_MASS) == pytest.approx(tank.saturation_pressure)


class TestEnergyBalanceTank:
    def test_the_loaded_state_agrees_with_the_isothermal_one(self):
        energy_balance = build(isothermal=False)
        isothermal = build(isothermal=True)
        internal_energy = energy_balance.initial_internal_energy

        assert energy_balance.get_temperature(
            FLUID_MASS, internal_energy
        ) == pytest.approx(TEMPERATURE)
        assert energy_balance.get_pressure(
            FLUID_MASS, internal_energy
        ) == pytest.approx(isothermal.get_pressure(FLUID_MASS), rel=1e-6)

    def test_draining_cools_the_tank(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        assert tank.get_temperature(fluid_mass, internal_energy) < TEMPERATURE

    def test_the_pressure_follows_the_temperature_down(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        assert tank.get_pressure(fluid_mass, internal_energy) < tank.get_pressure(
            FLUID_MASS, tank.initial_internal_energy
        )

    def test_the_decay_keeps_going(self):
        tank = build(isothermal=False)

        pressures = []
        fluid_mass, internal_energy = FLUID_MASS, tank.initial_internal_energy
        for _ in range(4):
            fluid_mass, internal_energy = drain(tank, 0.5, fluid_mass, internal_energy)
            pressures.append(tank.get_pressure(fluid_mass, internal_energy))

        assert pressures == sorted(pressures, reverse=True)

    def test_the_pressure_stays_on_the_saturation_curve(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        temperature = tank.get_temperature(fluid_mass, internal_energy)
        assert tank.get_pressure(fluid_mass, internal_energy) == pytest.approx(
            CP.PropsSI("P", "T", temperature, "Q", 0, FLUID), rel=1e-6
        )

    def test_the_density_follows_the_temperature(self):
        tank = build(isothermal=False)

        fluid_mass, internal_energy = drain(tank, 1.0)

        # A colder liquid is a denser one.
        assert tank.get_density(fluid_mass, internal_energy) > tank.get_density(
            FLUID_MASS, tank.initial_internal_energy
        )

    def test_it_asks_for_the_internal_energy(self):
        tank = build(isothermal=False)

        with pytest.raises(ValueError, match="initial_internal_energy"):
            tank.get_pressure(FLUID_MASS)

    def test_a_state_off_the_chart_says_so(self):
        tank = build(isothermal=False)

        with pytest.raises(ValueError, match="outside the range CoolProp"):
            tank.get_pressure(FLUID_MASS, -1e12)


class TestOutflowEnthalpy:
    def test_liquid_leaves_at_the_saturated_liquid_enthalpy(self):
        tank = build(isothermal=False)
        internal_energy = tank.initial_internal_energy

        temperature = tank.get_temperature(FLUID_MASS, internal_energy)
        assert tank.get_outflow_specific_enthalpy(
            FLUID_MASS, internal_energy
        ) == pytest.approx(CP.PropsSI("H", "T", temperature, "Q", 0, FLUID))

    def test_vapor_leaves_at_the_bulk_state(self):
        tank = build(isothermal=True)
        # Below the saturated vapor fill, so no liquid is left to draw on.
        vapor_mass = 0.5 * tank.saturated_vapor_density * VOLUME

        assert tank.get_outflow_specific_enthalpy(vapor_mass) == pytest.approx(
            CP.PropsSI("H", "T", TEMPERATURE, "D", vapor_mass / VOLUME, FLUID)
        )

    def test_an_empty_tank_carries_nothing_out(self):
        tank = build(isothermal=False)

        assert tank.get_outflow_specific_enthalpy(0.0, 0.0) == 0.0
