"""Observed order of accuracy of the biliquid time marching (Roache 1998)."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import machwave.simulation.biliquid as biliquid_simulation
from tests.test_simulations import motor_builders

# chamber transient from ignition: once the chamber settles, the truncation error
# drops below the CoolProp and CEA noise (about 1e-11 relative)
WINDOW = 0.0128  # s
DYER_WINDOW = 0.0032  # s, shorter since the Dyer element runs a CoolProp sweep
# small enough that the chamber never needs a substep
STEPS = (8e-5, 4e-5, 2e-5)


def build_state(*, smooth_thermochemistry: bool, dyer_oxidizer: bool = False):
    """The 1 kN engine at ignition, with the piston working on the top tank."""
    motor, params = motor_builders.build_1kn_biliquid_engine(
        dyer_oxidizer=dyer_oxidizer
    )
    # the CEA cache quantization makes the right-hand side piecewise constant and
    # hides the order of the scheme
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


def march(
    d_t: float, *, window: float = WINDOW, dyer_oxidizer: bool = False
) -> np.ndarray:
    """The engine state at the end of the window, marched at `d_t`."""
    state, external_pressure = build_state(
        smooth_thermochemistry=True, dyer_oxidizer=dyer_oxidizer
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        for _ in range(round(window / d_t)):
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

    # measured 4.6 to 4.7; the error is not yet purely fourth order at these steps,
    # so the band is wider above 4 than below
    assert np.all((observed_order > 3.5) & (observed_order < 5.0)), observed_order


def test_the_engine_state_converges_at_fourth_order_with_the_dyer_element() -> None:
    coarse, middle, fine = (
        march(d_t, window=DYER_WINDOW, dyer_oxidizer=True) for d_t in STEPS
    )

    observed_order = np.log2(np.abs(coarse - middle) / np.abs(middle - fine))

    # measured 4.47 to 4.54
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

    # start of the step plus its three later stages
    assert len(pressures) == 4
    assert len(set(pressures)) == 4
    assert pressures[0] == pytest.approx(state.chamber_pressure[0])
