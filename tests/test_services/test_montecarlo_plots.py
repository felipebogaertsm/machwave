"""Tests for plotting helpers in machwave.services.plots.montecarlo."""

import types

import numpy as np
import plotly.graph_objects as go
import pytest

import machwave.services.plots.montecarlo as montecarlo_plots


@pytest.fixture
def results() -> list[types.SimpleNamespace]:
    rng = np.random.default_rng(0)
    return [
        types.SimpleNamespace(
            total_impulse=float(total_impulse),
            time=np.linspace(0.0, 1.0, length),
            thrust=np.full(length, total_impulse),
        )
        for total_impulse, length in zip(rng.normal(100.0, 5.0, 20), range(5, 25))
    ]


def test_plot_histogram_returns_figure(results):
    fig = montecarlo_plots.plot_histogram(results, "total_impulse")

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1


def test_plot_histogram_with_kde_returns_figure(results):
    fig = montecarlo_plots.plot_histogram_with_kde(results, "total_impulse")

    assert isinstance(fig, go.Figure)
    assert [trace.name for trace in fig.data] == ["Histogram", "KDE"]


def test_plot_cdf_returns_figure(results):
    fig = montecarlo_plots.plot_cdf(results, "total_impulse", percentiles=(50,))

    assert isinstance(fig, go.Figure)
    assert fig.data[0].name == "CDF"


def test_plot_time_series_extremes_returns_figure(results):
    fig = montecarlo_plots.plot_time_series_extremes(results, "time", "thrust")

    assert isinstance(fig, go.Figure)
    assert [trace.name for trace in fig.data] == [
        "Lowest-mean scenario",
        "Highest-mean scenario",
        "Median-mean scenario",
    ]
