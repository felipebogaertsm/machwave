"""Order of accuracy of the biliquid time marching.

The whole engine state (chamber pressure, line masses, top tank internal
energy) goes through one Runge-Kutta step, so on a smooth stretch of the burn
the error falls with the fourth power of the step. The observed order comes
from three runs at halving steps, as in Roache (1998):

    p = log2(|y_4h - y_2h| / |y_2h - y_h|)
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.simulation.biliquid as biliquid_simulation
import machwave.simulation.biliquid.states as biliquid_states
from tests.test_simulations import motor_builders

# From ignition, well before any line runs dry. The window holds the chamber
# transient from the igniter pressure, which is where the truncation error is
# large enough to measure: once the chamber has settled the state drifts
# slowly and the error of every step falls to the CoolProp and CEA noise
# floor, about 1e-11 relative.
WINDOW = 0.0128  # s
# All below 1 / |lambda| of the chamber, so the stiffness never splits a step
# and the step the integrator takes halves with d_t.
STEPS = (8e-5, 4e-5, 2e-5)


def build_state(*, smooth_thermochemistry: bool):
    """
    The 1 kN engine with an SPI oxidizer element, from ignition.

    Dyer's element costs a CoolProp sweep per tank state, and SPI keeps the
    same coupling of flow to chamber and tank pressure. The top tank runs its
    energy balance and the piston works on it, so every part of the state
    vector moves.

    With `smooth_thermochemistry`, CEA is evaluated once and held: the
    propellant cache quantizes the chamber pressure and mixture ratio, which
    makes the right-hand side piecewise constant and hides the order of the
    scheme under its own steps.
    """
    motor, params = motor_builders.build_1kn_biliquid_engine()
    elements = motor.thrust_chamber.injector.elements
    motor.thrust_chamber.injector = thrust_chamber_models.Injector(
        elements={
            "oxidizer": thrust_chamber_models.InjectorElement(
                discharge_coefficient=elements["oxidizer"].discharge_coefficient,
                area=elements["oxidizer"].area,
            ),
            "fuel": elements["fuel"],
        }
    )
    if smooth_thermochemistry:
        properties = motor.propellant.evaluate(
            chamber_pressure=2.6e6,
            expansion_ratio=motor.thrust_chamber.nozzle.expansion_ratio,
            mixture_ratio=motor.propellant.oxidizer_to_fuel_ratio,
        )
        motor.propellant.evaluate = lambda **_: properties
    state = biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    return state, params.external_pressure


def march(d_t: float) -> np.ndarray:
    """The engine state at the end of the window, marched at `d_t`."""
    state, external_pressure = build_state(smooth_thermochemistry=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        for _ in range(round(WINDOW / d_t)):
            state.run_timestep(d_t, external_pressure)
    return np.array(
        [
            state.chamber_pressure[-1],
            state.fluid_mass_per_line["oxidizer"][-1],
            state.fluid_mass_per_line["fuel"][-1],
            state.internal_energy_per_line["oxidizer"],
        ]
    )


def test_the_engine_state_converges_at_fourth_order() -> None:
    coarse, middle, fine = (march(d_t) for d_t in STEPS)

    observed_order = np.log2(np.abs(coarse - middle) / np.abs(middle - fine))

    # Chamber pressure, oxidizer mass, fuel mass, top tank internal energy.
    # The Euler update this replaced gives 1.1 to 1.2 here. The coupled step
    # gives 4.6 to 4.7, and 4.6 to 4.8 one halving finer: the error is not yet
    # a pure h^4 at these steps, so the band is wider above 4 than below.
    assert np.all((observed_order > 3.5) & (observed_order < 5.0)), observed_order


def test_the_thermochemistry_is_evaluated_at_every_stage() -> None:
    state, external_pressure = build_state(smooth_thermochemistry=False)
    pressures = []
    evaluate = state.motor.propellant.evaluate

    def recording_evaluate(**kwargs):
        pressures.append(kwargs["chamber_pressure"])
        return evaluate(**kwargs)

    state.motor.propellant.evaluate = recording_evaluate
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        state.run_timestep(STEPS[0], external_pressure)

    # The start of the step and its three later stages.
    assert len(pressures) == 4
    assert len(set(pressures)) == 4
    assert pressures[0] == pytest.approx(state.chamber_pressure[0])


def test_a_stage_never_reads_a_line_drained_past_empty() -> None:
    """The step falls back to the capped depletion step instead."""
    state, external_pressure = build_state(smooth_thermochemistry=True)
    layout = biliquid_states._CoupledStateLayout(
        line_names=tuple(state.lines), energy_line_names=("oxidizer",)
    )
    drained = layout.pack(
        2e6,
        {"oxidizer": 1.0, "fuel": 0.0},
        {"oxidizer": state.internal_energy_per_line["oxidizer"]},
    )

    with pytest.raises(biliquid_states._StageLeftTheStateSpaceError):
        state._get_coupled_derivative(
            drained,
            layout=layout,
            is_feeding=True,
            external_pressure=external_pressure,
        )
