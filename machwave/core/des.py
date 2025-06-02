"""
This module groups pure functions that return the right-hand side of ODEs used
throughout Machwave. DEs stand for differential equations.

They are intentionally *stateless* and side-effect-free so that any numerical
integrator (RK4, RK45, implicit Euler, JAX-based solvers, etc.) can consume
them without modification.
"""

import numpy as np

from machwave.core.flow.isentropic import get_critical_pressure_ratio


def compute_chamber_pressure_mass_balance_srm(
    P0: float,
    Pe: float,
    Ab: float,
    V0: float,
    At: float,
    pp: float,
    k: float,
    R: float,
    T0: float,
    r: float,
    Cd: float = 1.0,
) -> tuple[float]:
    """
    Calculates the chamber pressure by solving Hans Seidel's differential
    equation.

    This differential equation was presented in Seidel's paper named
    "Transient Chamber Pressure and Thrust in Solid Rocket Motors", published
    in March, 1965.

    Args:
        P0 (float): Chamber pressure.
        Pe (float): External pressure.
        Ab (float): Burn area.
        V0 (float): Chamber free volume.
        At (float): Nozzle throat area.
        pp (float): Propellant density.
        k (float): Isentropic exponent of the mix.
        R (float): Gas constant per molecular weight.
        T0 (float): Flame temperature.
        r (float): Propellant burn rate.
        Cd (float): Discharge coefficient, default is 1.0.

    Returns:
        tuple[float]: Derivative of chamber pressure with respect to time.

    """
    critical_pressure_ratio = get_critical_pressure_ratio(k_mix=k)
    Pr = Pe / P0

    if Pr <= critical_pressure_ratio:  # choked
        H = (k**0.5) * (2 / (k + 1)) ** ((k + 1) / (2 * (k - 1)))
    else:  # sub-critical
        H = ((k / (k - 1)) ** 0.5) * Pr ** (1 / k) * (1 - Pr ** ((k - 1) / k)) ** 0.5

    m_dot_gen = pp * r * Ab
    m_dot_exit = Cd * P0 * At * H / (R * T0) ** 0.5

    dP0_dt = (R * T0 / V0) * (m_dot_gen - m_dot_exit)
    return (dP0_dt,)


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


def compute_point_mass_trajectory(
    y: float, v: float, T: float, D: float, M: float, g: float
) -> tuple[float, float]:
    """
    Returns the derivatives of elevation and velocity.

    Args:
        y (float): Instant elevation.
        v (float): Instant velocity.
        T (float): Instant thrust.
        D (float): Instant drag constant (Cd * A * rho / 2).
        M (float): Instant total mass.
        g (float): Instant acceleration of gravity.

    Returns:
        tuple[float, float]: Derivatives of elevation and velocity.
    """
    if v < 0:
        x = -1
    else:
        x = 1

    dv_dt = (T - x * D * (v**2)) / M - g
    dy_dt = v

    return (dy_dt, dv_dt)
