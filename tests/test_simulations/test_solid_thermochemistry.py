"""Solid motor thermochemistry follows the chamber pressure.

The solid state used to read the propellant's properties once, at
construction, and reuse them for every timestep. It now evaluates the
propellant at the chamber pressure of the step, the way the biliquid state
does. Formulations that carry pre-defined properties still see them returned
unchanged, which is what keeps their results identical.
"""

from __future__ import annotations

import copy
import dataclasses

import numpy as np
import pytest

import machwave.models.propellants.categories as propellant_categories
import machwave.simulation.solid as solid_simulation
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import run_simulation

TIMESTEP_COUNT = 5


def record_evaluations(propellant, monkeypatch, properties_for=None):
    """Record the arguments every `evaluate` call receives."""
    calls = []
    original = propellant.evaluate

    def recording_evaluate(chamber_pressure, expansion_ratio=8.0, mixture_ratio=None):
        calls.append(
            {
                "chamber_pressure": chamber_pressure,
                "expansion_ratio": expansion_ratio,
                "mixture_ratio": mixture_ratio,
            }
        )
        if properties_for is None:
            return original(chamber_pressure, expansion_ratio, mixture_ratio)
        return properties_for(chamber_pressure)

    monkeypatch.setattr(propellant, "evaluate", recording_evaluate)
    return calls


@pytest.fixture
def motor_and_params():
    motor, params = motor_builders.build_nero_motor()
    # The formulations are module-level singletons shared across tests.
    motor.propellant = copy.deepcopy(motor.propellant)
    return motor, params


def test_properties_are_evaluated_at_every_timestep(motor_and_params, monkeypatch):
    motor, params = motor_and_params
    calls = record_evaluations(motor.propellant, monkeypatch)
    state = solid_simulation.SolidMotorState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )

    for _ in range(TIMESTEP_COUNT):
        state.run_timestep(params.d_t, params.external_pressure)

    assert len(calls) == TIMESTEP_COUNT
    assert [call["chamber_pressure"] for call in calls] == (
        state.chamber_pressure[:TIMESTEP_COUNT]
    )
    assert {call["expansion_ratio"] for call in calls} == {
        motor.thrust_chamber.nozzle.expansion_ratio
    }


def test_chamber_pressure_reaches_the_propellant(motor_and_params, monkeypatch):
    motor, params = motor_and_params
    calls = record_evaluations(motor.propellant, monkeypatch)
    state = solid_simulation.SolidMotorState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )

    for _ in range(TIMESTEP_COUNT):
        state.run_timestep(params.d_t, params.external_pressure)

    # The motor pressurizes off the igniter, so the pressures must not repeat.
    chamber_pressures = [call["chamber_pressure"] for call in calls]
    assert len(set(chamber_pressures)) == TIMESTEP_COUNT


def test_pressure_dependent_properties_change_the_run(motor_and_params, monkeypatch):
    motor, params = motor_and_params
    constant_properties = motor.propellant.properties
    assert constant_properties is not None

    def properties_for(chamber_pressure):
        # A mild, monotonic drift with pressure, enough to move the thrust.
        scale = 1.0 + 0.02 * (chamber_pressure / 1e6)
        return dataclasses.replace(
            constant_properties,
            adiabatic_flame_temperature=(
                constant_properties.adiabatic_flame_temperature * scale
            ),
        )

    baseline = run_simulation(motor, params)
    record_evaluations(motor.propellant, monkeypatch, properties_for=properties_for)
    drifting = run_simulation(motor, params)

    common_length = min(baseline.thrust.size, drifting.thrust.size)
    assert common_length > 1
    assert not np.allclose(
        baseline.thrust[:common_length], drifting.thrust[:common_length]
    )


def test_propellant_without_pre_defined_properties_runs(motor_and_params, monkeypatch):
    motor, params = motor_and_params
    properties = motor.propellant.properties
    assert properties is not None

    propellant_without_properties = propellant_categories.SolidPropellant(
        name=motor.propellant.name,
        components=motor.propellant.components,
        mass_fractions=motor.propellant.mass_fractions,
        burn_rate_map=motor.propellant.burn_rate_map,
    )
    monkeypatch.setattr(
        propellant_without_properties,
        "evaluate",
        lambda chamber_pressure, expansion_ratio=8.0, mixture_ratio=None: properties,
    )
    motor.propellant = propellant_without_properties

    state = solid_simulation.SolidMotorState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    state.run_timestep(params.d_t, params.external_pressure)

    assert state.thrust[-1] > 0.0
