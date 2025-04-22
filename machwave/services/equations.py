from typing import Tuple

import numpy as np

from machwave.services.flow.isentropic import get_critical_pressure_ratio


def solve_cp_seidel(
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
) -> Tuple[float]:
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

    Returns:
        Tuple[float]: Derivative of chamber pressure with respect to time.

    """
    critical_pressure_ratio = get_critical_pressure_ratio(k_mix=k)

    if Pe / P0 <= critical_pressure_ratio:
        H = ((k / (k + 1)) ** 0.5) * ((2 / (k + 1)) ** (1 / (k - 1)))
    else:
        H = ((Pe / P0) ** (1 / k)) * (
            ((k / (k - 1)) * (1 - (Pe / P0) ** ((k - 1) / k))) ** 0.5
        )

    dP0_dt = ((R * T0 * Ab * pp * r) - (P0 * At * H * ((2 * R * T0) ** 0.5))) / V0

    return (dP0_dt,)


def solve_pressure_fed_lre_chamber_pressure(
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


def ballistics_ode(
    y: float, v: float, T: float, D: float, M: float, g: float
) -> Tuple[float, float]:
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
        Tuple[float, float]: Derivatives of elevation and velocity.
    """
    if v < 0:
        x = -1
    else:
        x = 1

    dv_dt = (T - x * D * (v**2)) / M - g
    dy_dt = v

    return (dy_dt, dv_dt)
