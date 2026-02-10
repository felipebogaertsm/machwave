"""
Liquid rocket engine chamber pressure mass balance differential equation.
"""

import numpy as np


def compute_chamber_pressure_mass_balance_lre(
    P0: float,
    R: float,
    T0: float,
    V0: float,
    At: float,
    k: float,
    m_dot_ox: float,
    m_dot_fuel: float,
) -> tuple[float]:
    """
    Calculates the chamber pressure by solving the mass balance equation for liquid
    rocket engines.

    Args:
        P0: Chamber pressure [Pa].
        R: Gas constant per molecular weight [J/(kg·K)].
        T0: Flame temperature [K].
        V0: Chamber free volume [m^3].
        At: Nozzle throat area [m^2].
        k: Isentropic exponent of the mix.
        m_dot_ox: Instantaneous oxidizer mass flow rate [kg/s].
        m_dot_fuel: Instantaneous fuel mass flow rate [kg/s].

    Returns:
        Derivative of chamber pressure with respect to time.
    """
    m_dot_out = (
        At
        * P0
        * k
        * (np.sqrt((2 / (k + 1)) ** ((k + 1) / (k - 1))))
        / (np.sqrt(k * R * T0))
    )
    m_dot_in = m_dot_ox + m_dot_fuel
    dP0_dt = (R * T0 / V0) * (m_dot_in - m_dot_out)
    return (dP0_dt,)
