"""A biliquid engine fed by a tank running an energy balance.

The tank's internal energy is a second state variable the integrator carries
beside its mass, so the tank cools as it drains and its pressure decays with
it, instead of holding flat until the liquid runs out.
"""

from __future__ import annotations

import CoolProp.CoolProp as CP
import numpy as np
import pytest

import machwave.models.feed_systems as feed_systems_models
import machwave.models.feed_systems.tank as tank_models
import machwave.simulation.biliquid as biliquid_simulation
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import (
    assert_recorded_arrays_aligned,
    run_simulation,
)

OXIDIZER_TANK = dict(
    fluid_name="N2O",
    volume=3.80e-3,
    temperature=300.0,
    initial_fluid_mass=2.78,
)
FUEL_TANK = dict(
    fluid_name="ETHANOL",
    volume=2.0e-3,
    temperature=300.0,
    initial_fluid_mass=1.55,
    isothermal=True,
)


def build(isothermal):
    motor, params = motor_builders.build_1kn_biliquid_engine()
    feed_system = motor.feed_system
    motor.feed_system = (
        feed_systems_models.StackedTankPressureFedFeedSystem.from_oxidizer_and_fuel(
            oxidizer_tank=tank_models.Tank(**OXIDIZER_TANK, isothermal=isothermal),
            fuel_tank=tank_models.Tank(**FUEL_TANK),
            piston_loss=feed_system.piston_loss,
            oxidizer_line_resistance=feed_system.lines["oxidizer"].resistance,
            fuel_line_resistance=feed_system.lines["fuel"].resistance,
        )
    )
    return motor, params


def end_oxidizer_volume(result):
    """Volume the oxidizer fills once the piston has swept the fuel out [m^3]."""
    motor, _ = build(isothermal=False)
    return motor.feed_system.get_tank_volumes(
        {name: float(series[-1]) for name, series in result.fluid_mass_per_line.items()}
    )["oxidizer"]


@pytest.fixture(scope="module")
def results():
    return {
        isothermal: run_simulation(*build(isothermal)) for isothermal in (True, False)
    }


def test_the_tank_pressure_decays_over_the_burn(results):
    pressure = results[False].tank_pressure_per_line["oxidizer"]

    assert pressure[-1] < 0.5 * pressure[0]


def test_the_tank_cools_over_the_burn(results):
    temperature = results[False].tank_temperature_per_line["oxidizer"]

    assert temperature[0] == pytest.approx(OXIDIZER_TANK["temperature"])
    assert temperature[-1] < temperature[0]


def test_the_decay_is_monotonic_while_the_tank_holds_liquid(results):
    result = results[False]
    tank = tank_models.Tank(**OXIDIZER_TANK, isothermal=False)
    # The saturated vapor density only falls as the tank cools, so a mass above
    # the vapor fill it started at holds liquid at any temperature it reaches.
    # Past that the outflow enthalpy steps by the latent heat as the last of
    # the liquid goes, and the decay picks up a jitter on the way out.
    # the piston grows the oxidizer volume, so take the vapor fill at its end volume
    oxidizer_volume = end_oxidizer_volume(result)
    two_phase = (
        result.fluid_mass_per_line["oxidizer"]
        > tank.saturated_vapor_density * oxidizer_volume
    )
    temperature = result.tank_temperature_per_line["oxidizer"][two_phase]

    assert two_phase.sum() > 1
    assert np.all(np.diff(temperature) <= 0.0)
    assert np.all(np.diff(result.tank_pressure_per_line["oxidizer"][two_phase]) <= 0.0)


def test_the_burn_reaches_thrust_termination(results):
    result = results[False]

    assert result.thrust_time > 0.0
    assert result.burn_time <= result.thrust_time
    assert np.all(np.isfinite(result.tank_temperature_per_line["fuel"]))


def test_an_isothermal_tank_holds_its_temperature(results):
    temperature = results[True].tank_temperature_per_line["oxidizer"]

    assert np.all(temperature == OXIDIZER_TANK["temperature"])


def test_the_engine_runs_longer_on_a_decaying_tank(results):
    # The same load pushes through a falling pressure, so it drains slower.
    assert results[False].burn_time > results[True].burn_time


def test_recorded_arrays_stay_aligned(results):
    assert_recorded_arrays_aligned(results[False])


def test_the_state_carries_the_energy_only_for_an_energy_balance():
    isothermal_motor, params = build(isothermal=True)
    energy_balance_motor, _ = build(isothermal=False)

    isothermal_state = biliquid_simulation.BiliquidEngineState(
        motor=isothermal_motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    energy_balance_state = biliquid_simulation.BiliquidEngineState(
        motor=energy_balance_motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )

    assert isothermal_state.internal_energy_per_line["oxidizer"] is None
    assert energy_balance_state.internal_energy_per_line["oxidizer"] == pytest.approx(
        energy_balance_motor.feed_system.lines["oxidizer"].tank.initial_internal_energy
    )


def test_draining_takes_the_outflow_enthalpy_out():
    motor, params = build(isothermal=False)
    state = biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    tank = motor.feed_system.lines["oxidizer"].tank
    internal_energy_before = state.internal_energy_per_line["oxidizer"]
    assert internal_energy_before is not None
    oxidizer_mass_before = state.fluid_mass_per_line["oxidizer"][-1]
    fuel_mass_before = state.fluid_mass_per_line["fuel"][-1]

    state.run_timestep(params.d_t, params.external_pressure)

    oxidizer_mass_after = state.fluid_mass_per_line["oxidizer"][-1]
    internal_energy_after = state.internal_energy_per_line["oxidizer"]
    mass_drained = oxidizer_mass_before - oxidizer_mass_after
    fuel_drained = fuel_mass_before - state.fluid_mass_per_line["fuel"][-1]
    assert mass_drained > 0.0
    assert fuel_drained > 0.0
    # trapezoidal estimate of the outflow enthalpy and piston work, second order
    swept_volume = fuel_drained / CP.PropsSI(
        "D", "T", FUEL_TANK["temperature"], "Q", 0, FUEL_TANK["fluid_name"]
    )
    volume_before = OXIDIZER_TANK["volume"]
    volume_after = volume_before + swept_volume

    def enthalpy_and_pressure(fluid_mass, internal_energy, volume):
        return (
            tank.get_outflow_specific_enthalpy(
                fluid_mass, internal_energy, mass_drained=0.0, volume=volume
            ),
            tank.get_pressure(fluid_mass, internal_energy, volume=volume),
        )

    enthalpy_before, pressure_before = enthalpy_and_pressure(
        oxidizer_mass_before, internal_energy_before, volume_before
    )
    enthalpy_after, pressure_after = enthalpy_and_pressure(
        oxidizer_mass_after, internal_energy_after, volume_after
    )
    energy_change = internal_energy_after - internal_energy_before
    assert energy_change == pytest.approx(
        -0.5 * (enthalpy_before + enthalpy_after) * mass_drained
        - 0.5 * (pressure_before + pressure_after) * swept_volume,
        rel=1e-6,
    )


def test_the_line_below_the_piston_runs_no_energy_balance():
    motor, params = build(isothermal=False)
    state = biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )

    state.run_timestep(params.d_t, params.external_pressure)

    assert state.internal_energy_per_line["fuel"] is None
    assert state.tank_temperature_per_line["fuel"][-1] == FUEL_TANK["temperature"]
