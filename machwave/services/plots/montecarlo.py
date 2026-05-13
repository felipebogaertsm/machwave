from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go
from scipy import stats as scipy_stats


def plot_histogram(
    results: list,
    property_name: str,
    x_axes_title: str = "x",
    **plotly_kwargs,
) -> None:
    """Histogram of a scalar property across all Monte Carlo results.

    Args:
        results: List of ``SimulationResult`` objects.
        property_name: Name of the scalar attribute to histogram.
        x_axes_title: Label for the x-axis.
        **plotly_kwargs: Additional kwargs passed to go.Histogram (e.g. nbinsx=50).
    """
    values = np.array([getattr(sim_result, property_name) for sim_result in results])

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=values, **plotly_kwargs))
    fig.update_xaxes(title_text=property_name or x_axes_title)
    fig.show()


def plot_histogram_with_kde(
    results: list,
    property_name: str,
    x_axes_title: str = "x",
    nbins: int = 30,
    kde_points: int = 200,
    **plotly_kwargs,
) -> None:
    """Histogram plus KDE curve for a scalar property across all results.

    Args:
        results: List of ``SimulationResult`` objects.
        property_name: Name of the attribute to plot.
        x_axes_title: Label for the x-axis.
        nbins: Number of bins in the histogram.
        kde_points: Number of points to compute the KDE curve.
        **plotly_kwargs: Additional kwargs for go.Histogram.
    """
    values = np.array([getattr(sim_result, property_name) for sim_result in results])

    kde = scipy_stats.gaussian_kde(values)
    xs = np.linspace(values.min(), values.max(), kde_points)
    kde_vals = kde(xs)

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=values,
            histnorm="probability density",
            nbinsx=nbins,
            opacity=0.5,
            name="Histogram",
            **plotly_kwargs,
        )
    )
    fig.add_trace(
        go.Scatter(x=xs, y=kde_vals, mode="lines", name="KDE", line=dict(width=2))
    )

    fig.update_layout(
        xaxis_title=property_name or x_axes_title,
        yaxis_title="Density",
        title=f"Histogram + '{property_name}' KDE",
    )
    fig.show()


def plot_cdf(
    results: list,
    property_name: str,
    x_axes_title: str = "x",
    percentiles: Sequence[int] = (5, 25, 50, 75, 95),
    **plotly_kwargs,
) -> None:
    """Empirical CDF of a scalar property across all results.

    Args:
        results: List of ``SimulationResult`` objects.
        property_name: Name of the attribute to plot.
        x_axes_title: Label for the x-axis.
        percentiles: Percentiles to mark on the plot.
        **plotly_kwargs: Additional kwargs passed to go.Scatter.
    """
    values = np.array([getattr(sim_result, property_name) for sim_result in results])
    sorted_vals = np.sort(values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

    pct_values = np.percentile(values, percentiles)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sorted_vals,
            y=cdf,
            mode="lines",
            name="CDF",
            **plotly_kwargs,
        )
    )

    for p, v in zip(percentiles, pct_values):
        fig.add_trace(
            go.Scatter(
                x=[v, v],
                y=[0, p / 100],
                mode="lines",
                line=dict(dash="dash"),
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[v],
                y=[p / 100],
                mode="markers+text",
                text=[f"{p}th"],
                textposition="top center",
                showlegend=False,
            )
        )

    fig.update_layout(
        xaxis_title=property_name or x_axes_title,
        yaxis_title="Cumulative Probability",
        title=f"CDF of '{property_name}'",
    )
    fig.update_yaxes(tickformat=".0%", range=[0, 1])

    fig.show()


def plot_time_series_extremes(
    results: list,
    time_property: str,
    series_property: str,
    x_axes_title: str = "time",
    title: str | None = None,
    **plotly_kwargs,
) -> None:
    """Plot the lowest-mean, highest-mean, and median-mean scenarios for a
    time-series property across all Monte Carlo results.

    Each curve is aligned against the longest time array, padding shorter
    series with NaN so they stop where their data ends.

    Args:
        results: List of ``SimulationResult`` objects.
        time_property: Name of the time-array attribute (e.g. ``"time"``).
        series_property: Name of the y(t) array attribute (e.g. ``"thrust"``).
        x_axes_title: Label for the x-axis.
        title: Plot title. If None, a default title is generated.
        **plotly_kwargs: Extra kwargs passed to go.Scatter.
    """
    all_times = []
    all_series = []

    for sim_result in results:
        t = np.asarray(getattr(sim_result, time_property))
        y = np.asarray(getattr(sim_result, series_property))
        all_times.append(t)
        all_series.append(y)

    lengths = [len(t) for t in all_times]
    idx_longest = int(np.argmax(lengths))
    common_time = all_times[idx_longest]
    Nmax = len(common_time)

    padded_series = []
    for y in all_series:
        n = len(y)
        if n < Nmax:
            padded = np.full(Nmax, np.nan, dtype=float)
            padded[:n] = y
            padded_series.append(padded)
        else:
            padded_series.append(y.copy())

    series_mat = np.vstack(padded_series)

    means = np.nanmean(series_mat, axis=1)

    i_min = int(np.nanargmin(means))
    i_max = int(np.nanargmax(means))
    median_of_means = np.median(means)
    i_med = int(np.nanargmin(np.abs(means - median_of_means)))

    y_min = series_mat[i_min]
    y_med = series_mat[i_med]
    y_max = series_mat[i_max]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=common_time,
            y=y_min,
            name="Lowest-mean scenario",
            line=dict(color="blue"),
            **plotly_kwargs,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=common_time,
            y=y_max,
            name="Highest-mean scenario",
            line=dict(color="red"),
            fill="tonexty",
            **plotly_kwargs,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=common_time,
            y=y_med,
            name="Median-mean scenario",
            line=dict(color="green", width=2, dash="dash"),
            **plotly_kwargs,
        )
    )

    fig.update_layout(
        xaxis_title=x_axes_title,
        yaxis_title=series_property,
        title=title
        or f"Extremes of '{series_property}' across {len(results)} scenarios",
    )

    fig.show()
