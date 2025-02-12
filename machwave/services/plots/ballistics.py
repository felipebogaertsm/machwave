import numpy as np
import plotly.graph_objects as go
import plotly.subplots


def ballistics_plots(
    t: np.ndarray, a: np.ndarray, v: np.ndarray, y: np.ndarray
) -> go.Figure:
    """
    Creates interactive plots for height, velocity, and acceleration over time.

    Args:
        t (np.ndarray): Time array.
        a (np.ndarray): Acceleration array.
        v (np.ndarray): Velocity array.
        y (np.ndarray): Height array.

    Returns:
        go.Figure: A Plotly figure with subplots for height, velocity, and acceleration.
    """
    fig = plotly.subplots.make_subplots(rows=3, cols=1, shared_xaxes=True)

    fig.add_trace(
        go.Scatter(x=t, y=y, mode="lines", name="Height", line=dict(color="blue")),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=t, y=v, mode="lines", name="Velocity", line=dict(color="green")),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=t[: len(a)],
            y=a,
            mode="lines",
            name="Acceleration",
            line=dict(color="red"),
        ),
        row=3,
        col=1,
    )

    fig.update_xaxes(title_text="Time (s)", row=3, col=1)
    fig.update_yaxes(title_text="Height (m)", row=1, col=1)
    fig.update_yaxes(title_text="Velocity (m/s)", row=2, col=1)
    fig.update_yaxes(title_text="Acceleration (m/s²)", row=3, col=1)

    fig.update_layout(title="Ballistics Plots", height=900)

    return fig
