"""Shared helpers for end-to-end internal ballistics simulation tests."""

from __future__ import annotations

import dataclasses
import warnings

import numpy as np

from machwave.models.motors import Motor
from machwave.simulation import (
    InternalBallisticsSimulation,
    InternalBallisticsSimulationParams,
    SimulationResult,
)


def run_simulation(
    motor: Motor, params: InternalBallisticsSimulationParams
) -> SimulationResult:
    """Run InternalBallisticsSimulation end-to-end, suppressing the empirical
    boundary-layer-loss warning that otherwise floods test output."""
    simulation = InternalBallisticsSimulation(motor=motor, params=params)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return simulation.run()


def assert_recorded_arrays_aligned(result: SimulationResult) -> None:
    """Every per-timestep series should have the same length as result.time.

    Fields marked with ``metadata={"non_aligned": True}`` are skipped (e.g.
    arrays filtered to a subset of timesteps, or with a non-time leading axis).
    """
    expected_length = result.time.size
    for field in dataclasses.fields(result):
        if field.metadata.get("non_aligned", False):
            continue
        value = getattr(result, field.name)
        if not isinstance(value, np.ndarray) or value.ndim < 1:
            continue
        actual_length = value.shape[0]
        assert actual_length == expected_length, (
            f"recorded array `{field.name}` has length {actual_length}, "
            f"expected {expected_length} (== result.time.size)"
        )
