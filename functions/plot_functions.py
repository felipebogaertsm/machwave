import numpy as np
import plotly.offline as pyo
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs


def interactive_plot(t, T, P0, Kn, m_prop):
    data = [go.Scatter(x=t,
                       y=P0 * 1e-6,
                       mode='lines',
                       name='lines'
                       )]
    layout = go.Layout(title='Pressure-Time Curve',
                       xaxis=dict(title='Time [s]'),
                       yaxis=dict(title='Pressure [MPa]'),
                       hovermode='closest')
    fig = go.Figure(data=data, layout=layout)
    pyo.plot(fig, filename='scatter.html')


def plot_performance(T, P0, t):
    """ Plots the chamber pressure and thrust in the same figure, saves to 'output' folder """
    fig1, ax1 = plt.subplots()

    ax1.set_xlim(0, t[-1])
    ax1.set_ylim(0, 1.05 * np.max(T))
    ax1.set_ylabel('Thrust [N]', color='#6a006a')
    ax1.set_xlabel('Time [s]')
    ax1.grid(color='#dc96ea', linestyle='-', linewidth='.4')
    ax1.plot(t, T, color='#6a006a', linewidth='1.5')
    ax1.tick_params(axis='y', labelcolor='k')

    ax2 = ax1.twinx()
    ax2.set_ylim(0, 1.1 * np.max(P0) * 1e-6)
    ax2.set_ylabel('Chamber Pressure [MPa]', color='#008141')
    ax2.grid(color='#a4ea96', linestyle='-', linewidth='.4')
    ax2.plot(t, P0 * 1e-6, color='#008141', linewidth='1.5')
    ax2.tick_params(axis='y', labelcolor='k')

    fig1.tight_layout()
    fig1.set_size_inches(10, 6, forward=True)
    fig1.savefig('output/pressure_thrust.png', dpi=300)


def plot_main(t, T, P0, Kn, m_prop):
    fig3 = plt.figure(3)
    fig3.suptitle('Motor Data', size='xx-large')
    gs1 = gs.GridSpec(nrows=2, ncols=2)

    ax1 = plt.subplot(gs1[0, 0])
    ax1.set_ylabel('Thrust [N]')
    ax1.set_xlabel('Time [s]')
    ax1.set_ylim(0, np.max(T) * 1.05)
    ax1.set_xlim(0, t[-1])
    ax1.grid(linestyle='-', linewidth='.4')
    ax1.plot(t, T, color='#6a006a', linewidth='1.5')

    ax2 = plt.subplot(gs1[0, 1])
    ax2.set_ylabel('Pressure [MPa]')
    ax2.yaxis.set_label_position('right')
    ax2.set_xlabel('Time [s]')
    ax2.set_ylim(0, np.max(P0) * 1e-6 * 1.05)
    ax2.set_xlim(0, t[-1])
    ax2.grid(linestyle='-', linewidth='.4')
    ax2.plot(t, P0 * 1e-6, color='#008141', linewidth='1.5')

    ax3 = plt.subplot(gs1[1, 0])
    ax3.set_ylabel('Klemmung')
    ax3.set_xlabel('Time [s]')
    ax3.set_ylim(0, np.max(Kn) * 1.05)
    ax3.set_xlim(0, t[-1])
    ax3.grid(linestyle='-', linewidth='.4')
    ax3.plot(t, Kn, color='b', linewidth='1.5')

    ax4 = plt.subplot(gs1[1, 1])
    ax4.set_ylabel('Propellant Mass [kg]')
    ax4.yaxis.set_label_position('right')
    ax4.set_xlabel('Time [s]')
    ax4.set_ylim(0, np.max(m_prop) * 1.05)
    ax4.set_xlim(0, t[-1])
    ax4.grid(linestyle='-', linewidth='.4')
    ax4.plot(t, m_prop, color='r', linewidth='1.5')

    fig3.set_size_inches(12, 8, forward=True)
    fig3.savefig('output/motor_plots.png', dpi=300)


def plot_mass_flux(t, grain_mass_flux):
    """ Plots and saves figure of the mass flux for all the grain segments """
    N, index = grain_mass_flux.shape
    for i in range(N):
        plt.plot(t, grain_mass_flux[i, :] * 1.42233e-3)
    plt.ylabel('Mass Flux [lb/s-in-in]')
    plt.xlabel('Time [s]')
    plt.ylim(0, np.max(grain_mass_flux) * 1.42233e-3 * 1.05)
    plt.xlim(0, t[-1])
    plt.grid(linestyle='-', linewidth='.4')
    plt.savefig('output/grain_mass_flux.png', dpi=300)
