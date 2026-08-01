"""A biliquid engine fed by a tank running an energy balance.

The tank's internal energy is a second state variable the integrator carries
beside its mass, so the tank cools as it drains and its pressure decays with
it, instead of holding flat until the liquid runs out.
"""

from __future__ import annotations

import numpy as np
import pytest

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


def build(isothermal):
    motor, params = motor_builders.build_1kn_biliquid_engine()
    motor.feed_system.oxidizer_tank = tank_models.Tank(
        **OXIDIZER_TANK, isothermal=isothermal
    )
    return motor, params


@pytest.fixture(scope="module")
def results():
    return {
        isothermal: run_simulation(*build(isothermal)) for isothermal in (True, False)
    }


def test_the_tank_pressure_decays_over_the_burn(results):
    pressure = results[False].oxidizer_tank_pressure

    assert pressure[-1] < 0.5 * pressure[0]


def test_the_tank_cools_over_the_burn(results):
    temperature = results[False].oxidizer_tank_temperature

    assert temperature[0] == pytest.approx(OXIDIZER_TANK["temperature"])
    assert temperature[-1] < temperature[0]


def test_the_decay_is_monotonic_while_the_tank_holds_liquid(results):
    result = results[False]
    tank = tank_models.Tank(**OXIDIZER_TANK, isothermal=False)
    # The saturated vapor density only falls as the tank cools, so a mass above
    # the vapor fill it started at holds liquid at any temperature it reaches.
    # Past that the outflow enthalpy steps by the latent heat as the last of
    # the liquid goes, and the decay picks up a jitter on the way out.
    two_phase = result.oxidizer_mass > tank.saturated_vapor_density * tank.volume
    temperature = result.oxidizer_tank_temperature[two_phase]

    assert two_phase.sum() > 1
    assert np.all(np.diff(temperature) <= 0.0)
    assert np.all(np.diff(result.oxidizer_tank_pressure[two_phase]) <= 0.0)


def test_an_isothermal_tank_holds_its_temperature(results):
    temperature = results[True].oxidizer_tank_temperature

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

    assert isothermal_state.oxidizer_internal_energy is None
    assert energy_balance_state.oxidizer_internal_energy == pytest.approx(
        energy_balance_motor.feed_system.oxidizer_tank.initial_internal_energy
    )


def test_draining_takes_the_outflow_enthalpy_out():
    motor, params = build(isothermal=False)
    state = biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    tank = motor.feed_system.oxidizer_tank
    internal_energy_before = state.oxidizer_internal_energy
    assert internal_energy_before is not None
    oxidizer_mass_before = state.oxidizer_mass[-1]

    state.run_timestep(params.d_t, params.external_pressure)

    mass_drained = oxidizer_mass_before - state.oxidizer_mass[-1]
    assert mass_drained > 0.0
    assert state.oxidizer_internal_energy == pytest.approx(
        internal_energy_before
        - mass_drained
        * tank.get_outflow_specific_enthalpy(
            oxidizer_mass_before, internal_energy_before
        )
    )
