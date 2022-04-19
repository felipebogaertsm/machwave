# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
This file contains the function that simulates the internal ballistics and
the rocket ballistics at the same time.
"""

import fluids.atmosphere as atm
import numpy as np

from models.ballistics import Ballistics
from models.internal_ballistics import InternalBallistics

from utils.isentropic_flow import (
    get_critical_pressure_ratio,
    get_divergent_correction_factor,
    get_opt_expansion_ratio,
    get_exit_pressure,
    get_operational_correction_factors,
    get_thrust_coeff,
    get_impulses,
)
from utils.solvers import solve_cp_seidel, ballistics_ode
from utils.units import get_pa_to_psi
from utils.geometric import get_cylinder_volume
from utils.atmospheric import (
    get_air_density_by_altitude,
    get_air_pressure_by_altitude,
    get_gravity_by_altitude,
)


def run_ballistics(
    prop,
    propellant,
    grain,
    structure,
    rocket,
    recovery,
    d_t,
    dd_t,
    initial_elevation_amsl,
    igniter_pressure,
    rail_length,
):
    """
    Runs the main loop of the SRM Solver program, returning all the internal
    ballistics and ballistics parameters as instances of the
    InternalBallistics and Ballistics classes.

    The function uses the Runge-Kutta 4th order numerical method for solving
    the differential equations.

    The variable names correspond to what they are commonly reffered to in
    books and papers related to Solid Rocket Propulsion.

    Therefore, PEP8's snake_case will not be followed rigorously.
    """

    # INITIAL CONDITIONS
    web = np.array([0])
    t = np.array([0])
    P_ext = np.array([])
    rho_air = np.array([])
    g = np.array([])
    P_0 = np.array([igniter_pressure])
    P_0_psi = np.array([get_pa_to_psi(igniter_pressure)])
    P_exit = np.array([])
    y = (np.array([0]),)
    v = np.array([0])
    mach_no = np.array([0])

    # ALLOCATING NUMPY ARRAYS FOR FUTURE CALCULATIONS
    m_vehicle = np.array([])  # total mass of the vehicle
    r = np.array([])  # burn rate
    V_0 = np.array([])  # empty chamber volume
    optimal_expansion_ratio = np.array([])  # opt. expansion ratio
    A_burn = np.array([])  # burn area
    V_prop = np.array([])  # propellant volume
    m_prop = np.array([])  # propellant mass
    n_kin, n_bl, n_tp, n_cf = (
        np.array([]),
        np.array([]),
        np.array([]),
        np.array([]),
    )  # thrust coefficient correction factors
    C_f, C_f_ideal, T = (
        np.array([]),
        np.array([]),
        np.array([]),
    )  # thrust coefficient and thrust

    # PRE CALCULATIONS
    # Critical pressure ratio:
    critical_pressure_ratio = get_critical_pressure_ratio(propellant.k_mix_ch)
    # Divergent correction factor:
    n_div = get_divergent_correction_factor(structure.divergent_angle)
    # Variables storing the apogee, apogee time and main chute ejection time:
    apogee, apogee_time, main_time = 0, -1, 0
    # Calculation of empty chamber volume (constant throughout the operation):
    empty_chamber_volume = get_cylinder_volume(
        structure.chamber_inner_diameter,
        structure.chamber_length,
    )

    # If the propellant mass is non zero, 'end_thrust' must be False,
    # since there is still thrust being produced.

    # After the propellant has finished burning and the thrust chamber has
    # stopped producing supersonic flow, 'end_thrust' is changed to a
    # True value and the internal ballistics section of the while loop below
    # stops running.

    end_thrust = False
    end_burn = False

    i = 0

    while y[i] >= 0 or m_prop[i - 1] > 0:
        t = np.append(t, t[i] + d_t)  # append new time value

        # Obtaining the value for the air density, the acceleration of
        # gravity and ext. pressure in function of the current altitude.
        rho_air = np.append(
            rho_air,
            get_air_density_by_altitude(y[i] + initial_elevation_amsl),
        )
        g = np.append(
            g,
            get_gravity_by_altitude(initial_elevation_amsl + y[i]),
        )
        P_ext = np.append(
            P_ext,
            get_air_pressure_by_altitude(initial_elevation_amsl + y[i]),
        )

        if end_thrust is False:
            # Calculating the burn area and propellant volume:
            A_burn_sum, V_prop_sum = 0, 0
            for j in range(grain.segment_count):
                if (
                    0.5 * (grain.outer_diameter - grain.core_diameter[j])
                ) >= web[i]:
                    A_burn_sum += grain.get_burn_area(web[i], j)
                    V_prop_sum += grain.get_propellant_volume(web[i], j)
                else:
                    A_burn_sum += 0
                    V_prop_sum += 0
            A_burn, V_prop = (
                np.append(A_burn, A_burn_sum),
                np.append(V_prop, V_prop_sum),
            )

            # Calculating the free chamber volume:
            V_0 = np.append(V_0, empty_chamber_volume - V_prop[i])
            # Calculating propellant mass:
            m_prop = np.append(m_prop, V_prop[i] * propellant.pp)

            # Get burn rate coefficients:
            r = np.append(r, propellant.get_burn_rate(P_0[i]))

            d_x = d_t * r[i]
            web = np.append(web, web[i] + d_x)

            k1 = solve_cp_seidel(
                P_0[i],
                P_ext[i],
                A_burn[i],
                V_0[i],
                structure.get_throat_area(),
                propellant.pp,
                propellant.k_mix_ch,
                propellant.R_ch,
                propellant.T0,
                r[i],
            )
            k2 = solve_cp_seidel(
                P_0[i] + 0.5 * k1 * d_t,
                P_ext[i],
                A_burn[i],
                V_0[i],
                structure.get_throat_area(),
                propellant.pp,
                propellant.k_mix_ch,
                propellant.R_ch,
                propellant.T0,
                r[i],
            )
            k3 = solve_cp_seidel(
                P_0[i] + 0.5 * k2 * d_t,
                P_ext[i],
                A_burn[i],
                V_0[i],
                structure.get_throat_area(),
                propellant.pp,
                propellant.k_mix_ch,
                propellant.R_ch,
                propellant.T0,
                r[i],
            )
            k4 = solve_cp_seidel(
                P_0[i] + 0.5 * k3 * d_t,
                P_ext[i],
                A_burn[i],
                V_0[i],
                structure.get_throat_area(),
                propellant.pp,
                propellant.k_mix_ch,
                propellant.R_ch,
                propellant.T0,
                r[i],
            )

            P_0 = np.append(
                P_0, P_0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * d_t
            )
            P_0_psi = np.append(P_0_psi, get_pa_to_psi(P_0[i]))

            optimal_expansion_ratio = np.append(
                optimal_expansion_ratio,
                get_opt_expansion_ratio(propellant.k_2ph_ex, P_0[i], P_ext[i]),
            )

            P_exit = np.append(
                P_exit,
                get_exit_pressure(
                    propellant.k_2ph_ex, structure.expansion_ratio, P_0[i]
                ),
            )

            (
                n_kin_atual,
                n_tp_atual,
                n_bl_atual,
            ) = get_operational_correction_factors(
                P_0[i],
                P_ext[i],
                P_0_psi[i],
                propellant,
                structure,
                critical_pressure_ratio,
                V_0[0],
                t[i],
            )

            n_kin = np.append(n_kin, n_kin_atual)
            n_tp = np.append(n_tp, n_tp_atual)
            n_bl = np.append(n_bl, n_bl_atual)

            n_cf = np.append(
                n_cf,
                (
                    (100 - (n_kin_atual + n_bl_atual + n_tp_atual))
                    * n_div
                    / 100
                    * propellant.n_ce
                ),
            )

            C_f_atual, C_f_ideal_atual = get_thrust_coeff(
                P_0[i],
                P_exit[i],
                P_ext[i],
                structure.expansion_ratio,
                propellant.k_2ph_ex,
                n_cf[i],
            )

            C_f = np.append(C_f, C_f_atual)
            C_f_ideal = np.append(C_f_ideal, C_f_ideal_atual)
            T = np.append(T, C_f[i] * structure.get_throat_area() * P_0[i])

            if m_prop[i] == 0 and end_burn is False:
                t_burnout = t[i]
                end_burn = True

            # This if statement changes 'end_thrust' to True if supersonic
            # flow is not achieved anymore.
            if P_0[i] <= P_ext[i] / critical_pressure_ratio:
                t_thrust = t[i]
                d_t = d_t * dd_t
                T_mean = np.mean(T)
                end_thrust = True

        # This else statement is necessary since the thrust and propellant
        # mass arrays are still being used inside the main while loop.

        # Therefore, it is necessary to append 0 to these arrays for the
        # ballistic part of the while loop to work correctly.
        else:
            m_prop = np.append(m_prop, 0)
            T = np.append(T, 0)

        # Entering first value for the vehicle mass and acceleration:
        if i == 0:
            m_vehicle_initial = (
                m_prop[0]
                + rocket.mass_wo_motor
                + structure.motor_structural_mass
            )
            m_vehicle = np.append(m_vehicle, m_vehicle_initial)
            acc = np.array(
                [
                    T[0]
                    / (
                        rocket.mass_wo_motor
                        + structure.motor_structural_mass
                        + m_prop[0]
                    )
                ]
            )

        # Appending the current vehicle mass, consisting of the motor
        # structural mass, mass without the motor and propellant mass.
        m_vehicle = np.append(
            m_vehicle,
            m_prop[i] + structure.motor_structural_mass + rocket.mass_wo_motor,
        )

        # Drag properties:
        if (
            v[i] < 0
            and y[i] <= recovery.main_chute_activation_height
            and m_prop[i] == 0
        ):
            if main_time == 0:
                main_time = t[i]
            A_drag = (
                (np.pi * (rocket.outer_diameter / 2) ** 2) * rocket.drag_coeff
                + (np.pi * recovery.drogue_diameter ** 2)
                * 0.25
                * recovery.drag_coeff_drogue
                + (np.pi * recovery.drag_coeff_main ** 2)
                * 0.25
                * recovery.drag_coeff_main
            )
        elif apogee_time >= 0 and t[i] >= apogee_time + recovery.drogue_time:
            A_drag = (
                np.pi * (rocket.outer_diameter / 2) ** 2
            ) * rocket.drag_coeff + (
                np.pi * recovery.drogue_diameter ** 2
            ) * 0.25 * recovery.drag_coeff_drogue
        else:
            A_drag = (
                (np.pi * rocket.outer_diameter ** 2) * rocket.drag_coeff * 0.25
            )

        D = (A_drag * rho_air[i]) * 0.5

        p1, l1 = ballistics_ode(y[i], v[i], T[i], D, m_vehicle[i], g[i])
        p2, l2 = ballistics_ode(
            y[i] + 0.5 * p1 * d_t,
            v[i] + 0.5 * l1 * d_t,
            T[i],
            D,
            m_vehicle[i],
            g[i],
        )
        p3, l3 = ballistics_ode(
            y[i] + 0.5 * p2 * d_t,
            v[i] + 0.5 * l2 * d_t,
            T[i],
            D,
            m_vehicle[i],
            g[i],
        )
        p4, l4 = ballistics_ode(
            y[i] + 0.5 * p3 * d_t,
            v[i] + 0.5 * l3 * d_t,
            T[i],
            D,
            m_vehicle[i],
            g[i],
        )

        y = np.append(y, y[i] + (1 / 6) * (p1 + 2 * (p2 + p3) + p4) * d_t)
        v = np.append(v, v[i] + (1 / 6) * (l1 + 2 * (l2 + l3) + l4) * d_t)
        acc = np.append(acc, (1 / 6) * (l1 + 2 * (l2 + l3) + l4))

        mach_no = np.append(mach_no, v[i] / atm.ATMOSPHERE_1976(y[i]).v_sonic)

        if y[i + 1] <= y[i] and m_prop[i] == 0 and apogee == 0:
            apogee = y[i]
            apogee_time = t[np.where(y == apogee)]

        i += 1

    if y[-1] < 0:
        y = np.delete(y, -1)
        v = np.delete(v, -1)
        acc = np.delete(acc, -1)
        t = np.delete(t, -1)

    v_rail = v[np.where(y >= rail_length)]
    v_rail = v_rail[0]
    y_burnout = y[np.where(v == np.max(v))]
    y_burnout = y_burnout[0]
    flight_time = t[-1]

    nozzle_eff = C_f / C_f_ideal  # nozzle efficiency

    I_total, I_sp = get_impulses(T_mean, t, t_burnout, m_prop)

    ballistics = Ballistics(
        t,
        y,
        v,
        acc,
        v_rail,
        y_burnout,
        mach_no,
        apogee_time[0],
        flight_time,
        P_ext,
    )

    optimal_grain_length = grain.get_optimal_segment_length()
    initial_port_to_throat = (grain.core_diameter[-1] ** 2) / (
        structure.nozzle_throat_diameter ** 2
    )

    burn_profile = grain.get_burn_profile(A_burn[A_burn != 0.0])
    Kn = A_burn / structure.get_throat_area()
    Kn_non_zero = Kn[Kn != 0.0]
    initial_to_final_kn = Kn_non_zero[0] / Kn_non_zero[-1]
    grain_mass_flux = grain.get_mass_flux_per_segment(r, propellant.pp, web)

    ib_parameters = InternalBallistics(
        t,
        P_0,
        T,
        T_mean,
        I_total,
        I_sp,
        t_burnout,
        t_thrust,
        nozzle_eff,
        optimal_expansion_ratio,
        V_prop,
        A_burn,
        Kn,
        m_prop,
        grain_mass_flux,
        optimal_grain_length,
        initial_port_to_throat,
        burn_profile,
        empty_chamber_volume,
        initial_to_final_kn,
        P_exit,
    )

    return ballistics, ib_parameters
