# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores the functions that solve isentropic flow equations.
"""

import numpy as np
import scipy.optimize

from rocketsolver.utils.geometric import get_circle_area


def get_critical_pressure_ratio(k_mix_ch):
    """
    Returns value of the critical pressure ratio.
    """
    return (2 / (k_mix_ch + 1)) ** (k_mix_ch / (k_mix_ch - 1))


def get_opt_expansion_ratio(k, P_0, P_ext):
    """
    Returns the optimal expansion ratio based on the current chamber pressure,
    specific heat ratio and external pressure.
    """
    exp_opt = (
        (((k + 1) / 2) ** (1 / (k - 1)))
        * ((P_ext / P_0) ** (1 / k))
        * np.sqrt(((k + 1) / (k - 1)) * (1 - (P_ext / P_0) ** ((k - 1) / k)))
    ) ** -1

    return exp_opt


def get_exit_mach(k: float, E: float):
    """
    Gets the exit Mach number of the nozzle flow.
    """
    exit_mach_no = scipy.optimize.fsolve(
        lambda x: (
            ((1 + 0.5 * (k - 1) * x**2) / (1 + 0.5 * (k - 1)))
            ** ((k + 1) / (2 * (k - 1)))
        )
        / x
        - E,
        [10],
    )
    return exit_mach_no[0]


def get_exit_pressure(k_2ph_ex, E, P_0):
    """
    Returns the exit pressure of the nozzle flow.
    """
    Mach_exit = get_exit_mach(k_2ph_ex, E)
    P_exit = P_0 * (1 + 0.5 * (k_2ph_ex - 1) * Mach_exit**2) ** (
        -k_2ph_ex / (k_2ph_ex - 1)
    )
    return P_exit


def get_thrust_coefficients(P_0, P_exit, P_external, E, k, n_cf):
    """
    Returns value for thrust coefficient based on the chamber pressure and
    correction factor.
    """
    P_r = P_exit / P_0
    Cf_ideal = np.sqrt(
        (2 * (k**2) / (k - 1))
        * ((2 / (k + 1)) ** ((k + 1) / (k - 1)))
        * (1 - (P_r ** ((k - 1) / k)))
    )
    Cf = (Cf_ideal + E * (P_exit - P_external) / P_0) * n_cf

    if Cf <= 0:
        Cf = 0
    if Cf_ideal <= 0:
        Cf_ideal = 0

    return Cf, Cf_ideal


def get_thrust_from_cf(
    C_f: float, P_0: float, nozzle_throat_area: float
) -> float:
    """
    :param C_f: instantaneous thrust coefficient, non ideal
    :param P_0: instantaneous chamber stagnation pressure, in Pascals
    :param nozzle_throat_area: nozzle throat area, in sq. meters
    :return: thrust in Newtons
    """
    return C_f * P_0 * nozzle_throat_area


def get_thrust_coefficient(
    P_0: float, thrust: float, nozzle_throat_area: float
):
    """
    :param P_0: instantaneous chamber stagnation pressure, in Pascals
    :param thrust: instantaneous thrust
    :param nozzle_throat_area: nozzle throat area, in sq. meters
    :return: thrust coefficient
    """
    return thrust / (P_0 * nozzle_throat_area)


def is_flow_choked(
    chamber_pressure: float,
    external_pressure: float,
    critical_pressure_ratio: float,
) -> bool:
    return chamber_pressure <= external_pressure / critical_pressure_ratio


def get_impulses(F_avg, t, t_burnout, m_prop):
    """
    Returns total and specific impulse, given the average thrust, time
    nparray and propellant mass nparray.
    """
    t = t[t <= t_burnout]
    index = np.where(t == t_burnout)

    m_prop = m_prop[: index[0][0]]

    I_total = F_avg * t[-1]
    I_sp = I_total / (m_prop[0] * 9.81)

    return I_total, I_sp


def get_total_impulse(average_thrust: float, thrust_time: float):
    """
    Returns the total impulse of the operation.
    """
    return average_thrust * thrust_time


def get_specific_impulse(total_impulse: float, initial_propellant_mass: float):
    """
    Returns the specific impulse of the operation.
    """
    return total_impulse / initial_propellant_mass / 9.81


def get_operational_correction_factors(
    P_0,
    P_external,
    P_0_psi,
    propellant,
    structure,
    critical_pressure_ratio,
    V0,
    t,
):
    """
    Returns kinetic, two-phase and boundary layer correction factors based
    on a015140.

    :param P_0: chamber stagnation pressure (Pa)
    :param P_external: external pressure
    :param P_0_psi: chamber pressure in psi
    :param propellant: propellant object
    :param structure: Structure object
    :param critical_pressure_ratio: critical pressure ratio
    :param V0: free chamber volume
    :param t: current time
    """

    # Kinetic losses
    if P_0_psi >= 200:
        n_kin = (
            33.3
            * 200
            * (propellant.Isp_frozen / propellant.Isp_shifting)
            / P_0_psi
        )
    else:
        n_kin = 0

    # Boundary layer and two phase flow losses
    if not is_flow_choked(P_0, P_external, critical_pressure_ratio):
        termC2 = 1 + 2 * np.exp(
            -structure.nozzle.material.C2
            * P_0_psi**0.8
            * t
            / ((structure.nozzle.throat_diameter / 0.0254) ** 0.2)
        )
        E_cf = 1 + 0.016 * structure.nozzle.expansion_ratio**-9
        n_bl = (
            structure.nozzle.material.C1
            * (
                (P_0_psi**0.8)
                / ((structure.nozzle.throat_diameter / 0.0254) ** 0.2)
            )
            * termC2
            * E_cf
        )

        C7 = (
            0.454
            * (P_0_psi**0.33)
            * (propellant.qsi_ch**0.33)
            * (
                1
                - np.exp(
                    -0.004
                    * (V0 / get_circle_area(structure.nozzle.throat_diameter))
                    / 0.0254
                )
                * (1 + 0.045 * structure.nozzle.throat_diameter / 0.0254)
            )
        )

        if 1 / propellant.M_ch >= 0.9:
            C4 = 0.5
            if structure.nozzle.throat_diameter / 0.0254 < 1:
                C3, C5, C6 = 9, 1, 1
            elif 1 <= structure.nozzle.throat_diameter / 0.0254 < 2:
                C3, C5, C6 = 9, 1, 0.8
            elif structure.nozzle.throat_diameter / 0.0254 >= 2:
                if C7 < 4:
                    C3, C5, C6 = 13.4, 0.8, 0.8
                elif 4 <= C7 <= 8:
                    C3, C5, C6 = 10.2, 0.8, 0.4
                elif C7 > 8:
                    C3, C5, C6 = 7.58, 0.8, 0.33
        elif 1 / propellant.M_ch < 0.9:
            C4 = 1
            if structure.nozzle.throat_diameter / 0.0245 < 1:
                C3, C5, C6 = 44.5, 0.8, 0.8
            elif 1 <= structure.nozzle.throat_diameter / 0.0254 < 2:
                C3, C5, C6 = 30.4, 0.8, 0.4
            elif structure.nozzle.throat_diameter / 0.0254 >= 2:
                if C7 < 4:
                    C3, C5, C6 = 44.5, 0.8, 0.8
                elif 4 <= C7 <= 8:
                    C3, C5, C6 = 30.4, 0.8, 0.4
                elif C7 > 8:
                    C3, C5, C6 = 25.2, 0.8, 0.33
        n_tp = C3 * (
            (propellant.qsi_ch * C4 * C7**C5)
            / (
                P_0_psi**0.15
                * structure.nozzle.expansion_ratio**0.08
                * (structure.nozzle.throat_diameter / 0.0254) ** C6
            )
        )
    else:
        n_tp = 0
        n_bl = 0

    return n_kin, n_tp, n_bl


def get_divergent_correction_factor(divergent_angle):
    """
    Returns the divergent nozzle correction factor given the half angle.
    """
    return 0.5 * (1 + np.cos(np.deg2rad(divergent_angle)))


def get_expansion_ratio(
    P_e: list, P_0: list, k: float, critical_pressure_ratio: float
):
    """
    Returns array of the optimal expansion ratio for each pressure ratio.

    :param P_e: pressure
    :param P_0: chamber stagnation pressure
    :param k: isentropic exponent
    :return: mean expansion ratio
    """
    E = np.zeros(np.size(P_0))

    for i in range(np.size(P_0)):
        if P_e / P_0[i] <= critical_pressure_ratio:
            pressure_ratio = P_e / P_0[i]
            E[i] = (
                ((k + 1) / 2) ** (1 / (k - 1))
                * pressure_ratio ** (1 / k)
                * ((k + 1) / (k - 1) * (1 - pressure_ratio ** ((k - 1) / k)))
                ** 0.5
            ) ** -1
        else:
            E[i] = 1
    return np.mean(E)
