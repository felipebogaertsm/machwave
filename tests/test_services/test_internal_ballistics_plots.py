"""Tests for plotting helpers in machwave.services.plots.internal_ballistics."""

import numpy as np
import plotly.graph_objects as go

import machwave.services.plots.internal_ballistics as ib_plots


class TestThrustCoefficientPlot:
    """Test the thrust_coefficient_plot helper."""

    def test_returns_figure_with_efficiency(self):
        """With show_efficiency=True, the figure has Cf_ideal, Cf_real, and η."""
        time = np.linspace(0, 1.0, 10)
        cf_ideal = np.linspace(1.5, 1.6, 10)
        cf_real = np.linspace(1.4, 1.5, 10)

        fig = ib_plots.thrust_coefficient_plot(
            time, cf_ideal, cf_real, show_efficiency=True
        )

        assert isinstance(fig, go.Figure)
        trace_names = [trace.name for trace in fig.data]
        assert trace_names == ["Cf (ideal)", "Cf (real)", "η = Cf_real / Cf_ideal"]

        # The η trace should be on the secondary y-axis (yaxis2);
        # the Cf traces should remain on the primary y-axis.
        cf_ideal_trace, cf_real_trace, eta_trace = fig.data
        assert cf_ideal_trace.yaxis == "y"
        assert cf_real_trace.yaxis == "y"
        assert eta_trace.yaxis == "y2"

        np.testing.assert_allclose(eta_trace.y, cf_real / cf_ideal)

    def test_returns_figure_without_efficiency(self):
        """With show_efficiency=False, only the Cf traces are present."""
        time = np.linspace(0, 1.0, 10)
        cf_ideal = np.linspace(1.5, 1.6, 10)
        cf_real = np.linspace(1.4, 1.5, 10)

        fig = ib_plots.thrust_coefficient_plot(
            time, cf_ideal, cf_real, show_efficiency=False
        )

        assert isinstance(fig, go.Figure)
        trace_names = [trace.name for trace in fig.data]
        assert trace_names == ["Cf (ideal)", "Cf (real)"]

        for trace in fig.data:
            assert trace.yaxis == "y"

    def test_efficiency_handles_zero_ideal_cf(self):
        """Division-by-zero in η is masked to NaN rather than raising."""
        time = np.array([0.0, 0.5, 1.0])
        cf_ideal = np.array([0.0, 1.5, 1.6])
        cf_real = np.array([0.0, 1.4, 1.5])

        fig = ib_plots.thrust_coefficient_plot(
            time, cf_ideal, cf_real, show_efficiency=True
        )

        eta_trace = fig.data[2]
        assert np.isnan(eta_trace.y[0])
        np.testing.assert_allclose(eta_trace.y[1:], cf_real[1:] / cf_ideal[1:])
