# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Plotting functions.
"""

import matplotlib.gridspec as gs
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.subplots


def performance_interactive_plot(ib_parameters):
    index = np.where(ib_parameters.t == ib_parameters.thrust_time)[0][0]
    pressure_color = "#008141"
    thrust_color = "#581845"

    figure = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])

    figure.add_trace(
        go.Scatter(
            x=ib_parameters.t[:index],
            y=ib_parameters.thrust[:index],
            name="Thrust",
            line=go.scatter.Line(color=thrust_color),
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=ib_parameters.t[:index],
            y=ib_parameters.P_0[:index] * 1e-6,
            name="Pressure",
            line=go.scatter.Line(color=pressure_color),
            yaxis="y2",
        ),
        secondary_y=True,
    )

    figure.update_layout(title_text="<b>Performance plots</b>")

    # Set x-axis title:
    figure.update_xaxes(title_text="Time (s)")

    # Set y-axes titles:
    figure.update_yaxes(
        title_text="<b>Thrust</b> (N)", secondary_y=False, color="#6a006a"
    )
    figure.update_yaxes(
        title_text="<b>Pressure</b> (MPa)", secondary_y=True, color="#008141"
    )

    return figure


def ballistics_plots(t, a, v, y, g):
    fig1 = plt.figure()

    plt.subplot(3, 1, 1)
    plt.ylabel("Height (m)")
    plt.grid(linestyle="-.")
    plt.plot(t, y, color="b")
    plt.subplot(3, 1, 2)
    plt.ylabel("Velocity (m/s)")
    plt.grid(linestyle="-.")
    plt.plot(t, v, color="g")
    plt.subplot(3, 1, 3)
    plt.ylabel("Acc (m/s2)")
    plt.xlabel("Time (s)")
    plt.grid(linestyle="-.")
    plt.plot(t[: len(a)], a, color="r")

    fig1.savefig("output/TrajectoryPlots.png", dpi=300)

    fig2 = plt.figure()

    plt.plot(t[: len(y)], y, color="b")
    plt.ylabel("Height (m)")
    plt.xlabel("Time (s)")
    plt.ylim(0, np.max(y) * 1.1)
    plt.xlim(0, t[-1])
    plt.grid()

    fig2.savefig("output/HeightPlot.png", dpi=300)

    fig3, ax3 = plt.subplots()

    ax3.set_xlim(0, t[-1])
    ax3.set_ylim(np.min(v * 3.6), np.max(v * 3.6) * 1.05)
    ax3.plot(t[: len(v)], v * 3.6, color="#009933")
    ax3.set_ylabel("Velocity (km/h)")
    ax3.set_xlabel("Time (s)")
    ax3.grid()

    ax4 = ax3.twinx()
    ax4.set_xlim(0, t[-1])
    ax4.set_ylim(np.min(a / g), np.max(a / g) * 1.3)
    ax4.plot(t[: len(a)], a / g, color="#ff6600")
    ax4.set_ylabel("Acceleration (g)")

    fig3.savefig("output/VelocityAcc.png", dpi=300)


def pressure_plot(t, P0, t_burnout):
    """
    Returns plotly figure with pressure data.
    """
    data = [
        go.Scatter(
            x=t[t <= t_burnout],
            y=P0 * 1e-6,
            mode="lines",
            name="lines",
            marker={"color": "#009933"},
        )
    ]
    layout = go.Layout(
        title="Pressure-time curve",
        xaxis=dict(title="Time [s]"),
        yaxis=dict(title="Pressure [MPa]"),
        hovermode="closest",
    )

    figure_plotly = go.Figure(data=data, layout=layout)
    figure_plotly.add_shape(
        type="line",
        x0=0,
        y0=np.mean(P0) * 1e-6,
        x1=t[-1],
        y1=np.mean(P0) * 1e-6,
        line={
            "color": "#ff0000",
        },
    )

    return figure_plotly


def thrust_plot(t, F):
    """
    Returns plotly figure with pressure data.
    """
    data = [
        go.Scatter(
            x=t, y=F, mode="lines", name="lines", marker={"color": "#6a006a"}
        )
    ]
    layout = go.Layout(
        title="Thrust-time curve",
        xaxis=dict(title="Time [s]"),
        yaxis=dict(title="Pressure [MPa]"),
        hovermode="closest",
    )
    figure_plotly = go.Figure(data=data, layout=layout)
    figure_plotly.add_shape(
        type="line",
        x0=0,
        y0=np.mean(F),
        x1=t[-1],
        y1=np.mean(F),
        line={
            "color": "#ff0000",
        },
    )
    return figure_plotly


def height_plot(t, y):
    """
    Returns plotly figure with altitude data.
    """
    data = [
        go.Scatter(
            x=t, y=y, mode="lines", name="lines", marker={"color": "#6a006a"}
        )
    ]
    layout = go.Layout(
        title="Altitude (AGL)",
        xaxis=dict(title="Time [s]"),
        yaxis=dict(title="Altitude [m]"),
        hovermode="closest",
    )
    figure_plotly = go.Figure(data=data, layout=layout)
    return figure_plotly


def velocity_plot(t, v):
    """
    Returns plotly figure with velocity data.
    """
    data = [
        go.Scatter(
            x=t, y=v, mode="lines", name="lines", marker={"color": "#6a006a"}
        )
    ]
    layout = go.Layout(
        title="Velocity plot",
        xaxis=dict(title="Time [s]"),
        yaxis=dict(title="Velocity [m/s]"),
        hovermode="closest",
    )
    figure_plotly = go.Figure(data=data, layout=layout)
    return figure_plotly


def performance_plot(F, P0, t, t_thrust):
    """
    Plots the chamber pressure and thrust in the same figure,
    saves to 'output' folder.
    """

    t = t[t <= t_thrust]
    F = F[: np.size(t)]
    P0 = P0[: np.size(t)]
    fig1, ax1 = plt.subplots()

    ax1.set_xlim(0, t[-1])
    ax1.set_ylim(0, 1.05 * np.max(F))
    ax1.set_ylabel("Thrust [N]", color="#6a006a")
    ax1.set_xlabel("Time [s]")
    ax1.grid(linestyle="-", linewidth=".4")
    ax1.plot(t, F, color="#6a006a", linewidth="1.5")
    ax1.tick_params(axis="y", labelcolor="k")

    ax2 = ax1.twinx()
    ax2.set_ylim(0, 1.15 * np.max(P0) * 1e-6)
    ax2.set_ylabel("Chamber Pressure [MPa]", color="#008141")
    ax2.plot(t, P0 * 1e-6, color="#008141", linewidth="1.5")
    ax2.tick_params(axis="y", labelcolor="k")

    fig1.tight_layout()
    fig1.savefig("output/PressureThrust.png", dpi=300)


def main_plot(t, F, P0, Kn, m_prop, t_burnout):
    """
    Returns pyplot figure and saves motor plots to 'output' folder.
    """

    t = t[t <= t_burnout]
    F = F[: np.size(t)]
    P0 = P0[: np.size(t)]
    Kn = Kn[: np.size(t)]
    m_prop = m_prop[: np.size(t)]
    main_figure = plt.figure(3)
    main_figure.suptitle("Motor Data", size="xx-large")
    gs1 = gs.GridSpec(nrows=2, ncols=2)

    ax1 = plt.subplot(gs1[0, 0])
    ax1.set_ylabel("Thrust [N]")
    ax1.set_xlabel("Time [s]")
    ax1.set_ylim(0, np.max(F) * 1.05)
    ax1.set_xlim(0, t[-1])
    ax1.grid(linestyle="-", linewidth=".4")
    ax1.plot(t, F, color="#6a006a", linewidth="1.5")

    ax2 = plt.subplot(gs1[0, 1])
    ax2.set_ylabel("Pressure [MPa]")
    ax2.yaxis.set_label_position("right")
    ax2.set_xlabel("Time [s]")
    ax2.set_ylim(0, np.max(P0) * 1e-6 * 1.05)
    ax2.set_xlim(0, t[-1])
    ax2.grid(linestyle="-", linewidth=".4")
    ax2.plot(t, P0 * 1e-6, color="#008141", linewidth="1.5")

    ax3 = plt.subplot(gs1[1, 0])
    ax3.set_ylabel("Klemmung")
    ax3.set_xlabel("Time [s]")
    ax3.set_ylim(0, np.max(Kn) * 1.05)
    ax3.set_xlim(0, t[-1])
    ax3.grid(linestyle="-", linewidth=".4")
    ax3.plot(t[: len(Kn)], Kn, color="b", linewidth="1.5")

    ax4 = plt.subplot(gs1[1, 1])
    ax4.set_ylabel("Propellant Mass [kg]")
    ax4.yaxis.set_label_position("right")
    ax4.set_xlabel("Time [s]")
    ax4.set_ylim(0, np.max(m_prop) * 1.05)
    ax4.set_xlim(0, t[-1])
    ax4.grid(linestyle="-", linewidth=".4")
    ax4.plot(t[: len(m_prop)], m_prop, color="r", linewidth="1.5")

    main_figure.set_size_inches(12, 8, forward=True)
    main_figure.savefig("output/MotorPlots.png", dpi=300)
    return main_figure


def mass_flux_plot(t, grain_mass_flux, t_burnout):
    """Plots and saves figure of the mass flux for all the grain segments"""
    t = t[t <= t_burnout]
    t = np.append(t, t[-1])
    grain_mass_flux = grain_mass_flux
    N, index = grain_mass_flux.shape
    mass_flux_figure = plt.figure()
    for i in range(N):
        plt.plot(t[: len(grain_mass_flux[i])], grain_mass_flux[i] * 1.42233e-3)
    plt.ylabel("Mass Flux [lb/s-in-in]")
    plt.xlabel("Time [s]")
    plt.ylim(0, np.max(grain_mass_flux) * 1.42233e-3 * 1.05)
    plt.xlim(0, t[-1])
    plt.grid(linestyle="-", linewidth=".4")
    mass_flux_figure.savefig("output/GrainMassFlux.png", dpi=300)
    return mass_flux_figure
