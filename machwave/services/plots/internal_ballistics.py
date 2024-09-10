import numpy as np
import plotly.graph_objects as go
import plotly.subplots


def thrust_pressure_plot(
    time: np.ndarray, thrust: np.ndarray, chamber_pressure: np.ndarray
) -> go.Figure:
    """
    Generates an interactive plot with thrust and chamber pressure over time.

    Args:
        time (np.ndarray): Time array.
        thrust (np.ndarray): Thrust array.
        chamber_pressure (np.ndarray): Chamber pressure array.

    Returns:
        go.Figure: A Plotly figure with thrust and pressure data over time.
    """
    figure = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])

    figure.add_trace(
        go.Scatter(
            x=time,
            y=thrust,
            mode="lines",
            name="Thrust",
            line=dict(color="#6a006a"),
        ),
        secondary_y=False,
    )

    figure.add_trace(
        go.Scatter(
            x=time,
            y=chamber_pressure * 1e-6,
            mode="lines",
            name="Chamber Pressure",
            line=dict(color="#008141"),
        ),
        secondary_y=True,
    )

    figure.update_layout(title_text="<b>Thrust and Pressure vs Time</b>")

    figure.update_xaxes(title_text="Time (s)")
    figure.update_yaxes(
        title_text="<b>Thrust</b> (N)", secondary_y=False, color="#6a006a"
    )
    figure.update_yaxes(
        title_text="<b>Chamber Pressure</b> (MPa)",
        secondary_y=True,
        color="#008141",
    )

    return figure


def mass_flux_plot(time: np.ndarray, mass_flux: np.ndarray) -> go.Figure:
    """
    Generates an interactive plot for mass flux across multiple segments.

    Args:
        time (np.ndarray): Time array.
        mass_flux (np.ndarray): A 2D array where each row represents mass flux data for a segment.

    Returns:
        go.Figure: A Plotly figure with mass flux data for each segment.
    """
    figure = go.Figure()

    for i in range(len(mass_flux)):
        figure.add_trace(
            go.Scatter(
                x=time,
                y=mass_flux[i, :],
                name="Segment " + str(i + 1),
            )
        )

    figure.update_layout(title="Segment Mass Flux")

    return figure
