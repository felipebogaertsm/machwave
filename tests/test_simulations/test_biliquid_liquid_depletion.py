"""The oxidizer line of a biliquid engine as its tank runs out of liquid."""

from __future__ import annotations

import dataclasses
import warnings

import CoolProp.CoolProp as CP
import pytest

import machwave.models.feed_systems.lines as line_models
import machwave.simulation.biliquid as biliquid_simulation
import machwave.simulation.biliquid.states as biliquid_states
from tests.test_simulations import motor_builders

TANK_TEMPERATURE = 300.0  # K, the 1 kN engine loading
OXIDIZER_TANK_VOLUME = 3.80e-3  # m^3
# far below the liquid one step draws at about 0.5 kg/s
LIQUID_LEFT = 1e-5  # kg
# lasts many steps at that flow
LIQUID_FOR_MANY_STEPS = 0.1  # kg


def build_state(liquid_mass):
    """The 1 kN engine at ignition, its oxidizer tank holding `liquid_mass`."""
    liquid_density = CP.PropsSI("D", "T", TANK_TEMPERATURE, "Q", 0, "N2O")
    vapor_density = CP.PropsSI("D", "T", TANK_TEMPERATURE, "Q", 1, "N2O")
    oxidizer_mass = vapor_density * OXIDIZER_TANK_VOLUME + liquid_mass * (
        1.0 - vapor_density / liquid_density
    )
    motor, params = motor_builders.build_1kn_biliquid_engine(
        oxidizer_mass=oxidizer_mass
    )
    state = biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    return state, params


def get_oxidizer_flow_at_density(state, params, density):
    """Oxidizer line flow at ignition with the tank outlet at `density` [kg/s]."""
    motor = state.motor
    inlet_states = motor.feed_system.get_inlet_states(
        {
            name: line_models.LineState(
                fluid_mass=state.fluid_mass_per_line[name][0],
                internal_energy=state.internal_energy_per_line[name],
            )
            for name in state.lines
        }
    )
    inlet_states["oxidizer"] = dataclasses.replace(
        inlet_states["oxidizer"], density=density
    )
    return biliquid_states.get_injector_mass_flows(
        state.chamber_pressure[0],
        injector=motor.thrust_chamber.injector,
        lines=state.lines,
        inlet_states=inlet_states,
        line_masses={
            name: series[0] for name, series in state.fluid_mass_per_line.items()
        },
        is_feeding=True,
        d_t=params.d_t,
    )["oxidizer"]


def run_one_step(state, params):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        state.run_timestep(params.d_t, params.external_pressure)


def test_a_line_whose_liquid_runs_out_within_the_step_draws_the_tank_vapor():
    state, params = build_state(LIQUID_LEFT)
    vapor_density = CP.PropsSI("D", "T", TANK_TEMPERATURE, "Q", 1, "N2O")
    vapor_flow = get_oxidizer_flow_at_density(state, params, vapor_density)

    run_one_step(state, params)

    oxidizer_flow = state.mass_flow_rate_per_line["oxidizer"][-1]
    assert oxidizer_flow == pytest.approx(vapor_flow, rel=1e-12)
    assert oxidizer_flow * params.d_t > LIQUID_LEFT


def test_a_line_with_liquid_for_the_whole_step_draws_liquid():
    state, params = build_state(LIQUID_FOR_MANY_STEPS)
    liquid_density = CP.PropsSI("D", "T", TANK_TEMPERATURE, "Q", 0, "N2O")
    liquid_flow = get_oxidizer_flow_at_density(state, params, liquid_density)

    run_one_step(state, params)

    assert state.mass_flow_rate_per_line["oxidizer"][-1] == pytest.approx(
        liquid_flow, rel=1e-12
    )
