import types

import numpy as np
import pytest

import machwave.montecarlo.base as montecarlo_base


def _simulation_with_values(values: np.ndarray) -> montecarlo_base.MonteCarloSimulation:
    simulation = montecarlo_base.MonteCarloSimulation([], len(values), object)
    simulation.results = [types.SimpleNamespace(total_impulse=v) for v in values]
    return simulation


def test_mode_of_continuous_samples_tracks_the_density_peak() -> None:
    """Mode of distinct normal samples sits near the center, not at the minimum."""
    rng = np.random.default_rng(0)
    values = rng.normal(1000.0, 50.0, 200)

    stats = _simulation_with_values(values).get_property_stats("total_impulse")

    assert stats["mode"] > values.min()
    assert stats["mode"] == pytest.approx(1000.0, abs=25.0)


@pytest.mark.filterwarnings("ignore:Precision loss:RuntimeWarning")
def test_mode_of_constant_samples_is_the_constant() -> None:
    values = np.full(10, 42.0)

    stats = _simulation_with_values(values).get_property_stats("total_impulse")

    assert stats["mode"] == 42.0
