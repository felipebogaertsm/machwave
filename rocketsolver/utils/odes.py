# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores solvers called inside the simulations.
"""

from rocketsolver.utils.isentropic_flow import get_critical_pressure_ratio


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
):
    """
    Calculates the chamber pressure by solving Hans Seidel's differential
    equation.

    This differential equation was presented in Seidel's paper named
    "Transient Chamber Pressure and Thrust in Solid Rocket Motors", published
    in March, 1965.

    :param P0: chamber pressure
    :param Pe: external pressure
    :param Ab: burn area
    :param V0: chamber free volume
    :param At: nozzle throat area
    :param pp: propellant density
    :param k: isentropic exponent of the mix
    :param R: gas constant per molecular weight
    :param T0: flame temperature
    :param r: propellant burn rate
    :return: dP0 / dt
    :rtype: float
    """
    critical_pressure_ratio = get_critical_pressure_ratio(k_mix_ch=k)

    if Pe / P0 <= critical_pressure_ratio:
        H = ((k / (k + 1)) ** 0.5) * ((2 / (k + 1)) ** (1 / (k - 1)))
    else:
        H = ((Pe / P0) ** (1 / k)) * (
            ((k / (k - 1)) * (1 - (Pe / P0) ** ((k - 1) / k))) ** 0.5
        )

    dP0_dt = (
        (R * T0 * Ab * pp * r) - (P0 * At * H * ((2 * R * T0) ** 0.5))
    ) / V0

    return dP0_dt


def ballistics_ode(y, v, T, D, M, g):
    """
    Returns dy_dt and dv_dt.

    :param y: instant elevation
    :param v: instant velocity
    :param T: instant thrust
    :param D: instant drag constant (Cd * A * rho / 2)
    :param M: instant total mass
    :param g: instant acceleration of gravity
    :return: dy_dt, dv_dt
    :rtype: float, float
    """
    if v < 0:
        x = -1
    else:
        x = 1

    dv_dt = (T - x * D * (v**2)) / M - g
    dy_dt = v

    return dy_dt, dv_dt
