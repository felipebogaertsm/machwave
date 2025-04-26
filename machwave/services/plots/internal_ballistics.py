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


def plot_bipropellant_tank_profiles(
    time: np.ndarray,
    oxidizer_tank_pressure: np.ndarray,
    fuel_tank_pressure: np.ndarray,
    oxidizer_tank_mass: np.ndarray,
    fuel_tank_mass: np.ndarray,
) -> go.Figure:
    """
    Generates an interactive double chart:
      - Left subplot: oxidizer & fuel tank pressures (in MPa) vs time
      - Right subplot: oxidizer & fuel tank masses (in kg) vs time

    Args:
        time: Time array [s].
        oxidizer_tank_pressure: Oxidizer tank pressure array [Pa].
        fuel_tank_pressure: Fuel tank pressure array [Pa].
        oxidizer_tank_mass: Oxidizer tank mass array [kg].
        fuel_tank_mass: Fuel tank mass array [kg].
    """
    # Create 1×2 layout
    fig = plotly.subplots.make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Tank Pressures", "Tank Masses"),
        horizontal_spacing=0.1,
    )

    # — Left: Pressures (converted to MPa) —
    fig.add_trace(
        go.Scatter(
            x=time,
            y=oxidizer_tank_pressure * 1e-6,
            mode="lines",
            name="Oxidizer Pressure",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=time, y=fuel_tank_pressure * 1e-6, mode="lines", name="Fuel Pressure"
        ),
        row=1,
        col=1,
    )

    # — Right: Masses —
    fig.add_trace(
        go.Scatter(x=time, y=oxidizer_tank_mass, mode="lines", name="Oxidizer Mass"),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(x=time, y=fuel_tank_mass, mode="lines", name="Fuel Mass"),
        row=1,
        col=2,
    )

    # Axis labels
    fig.update_xaxes(title_text="Time (s)", row=1, col=1)
    fig.update_yaxes(title_text="Pressure (MPa)", row=1, col=1)
    fig.update_xaxes(title_text="Time (s)", row=1, col=2)
    fig.update_yaxes(title_text="Mass (kg)", row=1, col=2)

    # Overall layout tweaks
    fig.update_layout(
        title_text="<b>Bipropellant Tank Profiles</b>",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=80, b=50),
    )

    return fig
