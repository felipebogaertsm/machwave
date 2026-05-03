"""Shared helpers for end-to-end internal ballistics simulation tests."""

from __future__ import annotations

import warnings
from typing import NamedTuple

import numpy as np

from machwave.models.motors import Motor
from machwave.simulation import (
    InternalBallisticsSimulation,
    InternalBallisticsSimulationParams,
)
from machwave.states import MotorState


class SimulationResult(NamedTuple):
    time: np.ndarray
    state: MotorState


def run_simulation(
    motor: Motor, params: InternalBallisticsSimulationParams
) -> SimulationResult:
    """Run InternalBallisticsSimulation end-to-end, suppressing the empirical
    boundary-layer-loss warning that otherwise floods test output."""
    simulation = InternalBallisticsSimulation(motor=motor, params=params)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        time, state = simulation.run()
    return SimulationResult(time=time, state=state)


def assert_recorded_arrays_aligned(
    state: MotorState, attribute_names: tuple[str, ...]
) -> None:
    """Every per-timestep series should have the same length as state.t."""
    expected_length = len(state.t)
    for name in attribute_names:
        actual_length = len(getattr(state, name))
        assert actual_length == expected_length, (
            f"recorded array `{name}` has length {actual_length}, "
            f"expected {expected_length} (== len(state.t))"
        )
