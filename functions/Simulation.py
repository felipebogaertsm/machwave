import numpy as np
import fluids.atmosphere as atm

from functions.Propellant import *
from functions.InternalBallistics import *
from functions.Ballistics import *


def run_ballistics(prop, propellant, grain, structure, rocket, dt, P_igniter, P_ext):
    # Initial conditions:
    web = np.array([0])
    t = np.array([0])
    P0, P0_psi, P_exit = np.array([P_igniter]), np.array([P_igniter]) * 1.45e-4, np.array([P_ext])
    y, v = np.array([0]), np.array([0])
    Mach = np.array([0])
    h0 = 4
    m_vehicle = np.array([])

    r = np.array([])
    V0 = np.array([])
    Exp_opt = np.array([])
    A_burn, V_prop = np.array([]), np.array([])
    m_prop = np.array([])
    n_kin, n_bl, n_tp, n_cf = np.array([]), np.array([]), np.array([]), np.array([])
    C_f, T = np.array([]), np.array([])
    critical_pressure_ratio = (2 / (propellant.k_mix_ch + 1)) ** (propellant.k_mix_ch /
                                                                  (propellant.k_mix_ch - 1))

    # Recovery data
    # Launch rail length [m]
    rail_length = 5
    # Time after apogee for drogue parachute activation [s]
    drogue_time = 1
    # Drogue drag coefficient
    Cd_drogue = 1.75
    # Drogue effective diameter [m]
    D_drogue = 1.25
    # Main parachute drag coefficient [m]
    Cd_main = 2
    # Main parachute effective diameter [m]
    D_main = 2.66
    # Main parachute height activation [m]
    main_chute_activation_height = 500

    apogee, apogee_time, main_time = 0, - 1, 0

    V_empty = np.pi * structure.L_chamber * (structure.D_chamber ** 2) / 4

    end_thrust = False
    i = 0
    while y[i] >= 0 or m_prop[i - 1] > 0:

        t = np.append(t, t[i] + dt)

        if end_thrust is False:

            # Calculating the burn area and propellant volume:
            A_burn_sum, V_prop_sum = 0, 0
            for j in range(grain.N):
                if 0.5 * (grain.D_grain - grain.D_core[j]) >= web[i]:
                    A_burn_sum += get_burn_area(grain, web[i], j)
                    V_prop_sum += get_propellant_volume(grain, web[i], j)
                else:
                    A_burn_sum += 0
                    V_prop_sum += 0
            A_burn, V_prop = np.append(A_burn, A_burn_sum), np.append(V_prop, V_prop_sum)
            # Calculating the free chamber volume:
            V0 = np.append(V0, V_empty - V_prop[i])
            # Calculating propellant mass:
            m_prop = np.append(m_prop, V_prop[i] * propellant.pp)

            # Get burn rate coefficients:
            a, n = get_burn_rate_coefs(prop, P0[i])
            # If 'a' and 'n' are negative, exit the program (lacking burn rate date for the current value of P0).
            if a < 0:
                exit()

            r = np.append(r, (a * (P0[i] * 1e-6) ** n) * 1e-3)
            dx = dt * r[i]
            web = np.append(web, web[i] + dx)

            k1 = solve_cp_seidel(P0[i], P_ext, A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
            k2 = solve_cp_seidel(P0[i] + 0.5 * k1 * dt, P_ext, A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
            k3 = solve_cp_seidel(P0[i] + 0.5 * k2 * dt, P_ext, A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
            k4 = solve_cp_seidel(P0[i] + 0.5 * k3 * dt, P_ext, A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])

            P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)
            P0_psi = np.append(P0_psi, P0[i] * 1.45e-4)

            k = propellant.k_2ph_ex
            Exp_opt = np.append(Exp_opt, (((k + 1) / 2) ** (1 / (k - 1)) * critical_pressure_ratio ** (1 / k) * (
                    (k + 1) / (k - 1) * (1 - critical_pressure_ratio ** ((k - 1) / k))) ** 0.5) ** -1)
            # P_exit = np.append(P_exit, get_exit_pressure(propellant.k_2ph_ex, structure.Exp_ratio, P0))
            n_div = 0.5 * (1 + np.cos(np.deg2rad(structure.Div_angle)))
            n_kin_atual, n_tp_atual, n_bl_atual = get_operational_correction_factors(P0[i], P_ext, P0_psi[i],
                                                                                     propellant, structure,
                                                                                     critical_pressure_ratio, V0[0],
                                                                                     t[i])
            n_kin, n_tp, n_bl = np.append(n_kin, n_kin_atual), np.append(n_tp, n_tp_atual), np.append(n_bl, n_bl_atual)
            n_cf = np.append(n_cf, ((100 - (n_kin_atual + n_bl_atual + n_tp_atual)) * n_div / 100))

            C_f = np.append(C_f, get_thrust_coefficient(P0[i], P_ext, structure.Exp_ratio, propellant.k_2ph_ex, n_cf[i]))
            T = np.append(T, C_f[i] * structure.A_throat * P0[i])

            if P0[i] <= P_ext / critical_pressure_ratio:
                end_thrust = True

        else:
            m_prop = np.append(m_prop, 0)
            T = np.append(T, 0)

        # Entering first value for the vehicle mass:
        if i == 0:
            m_vehicle_initial = m_prop[0] + rocket.mass_wo_motor + structure.m_motor
            m_vehicle = np.append(m_vehicle, m_vehicle_initial)
            acc = np.array([T[0] * (rocket.mass_wo_motor + structure.m_motor + m_prop[0])])

        rho_air = atm.ATMOSPHERE_1976(y[i] + h0).rho
        g = atm.ATMOSPHERE_1976.gravity(h0 + y[i])

        m_vehicle = np.append(m_vehicle, m_prop[i] + structure.m_motor + rocket.mass_wo_motor)

        # Drag properties:
        if v[i] < 0 and y[i] <= main_chute_activation_height and m_prop[i] == 0:
            if main_time == 0:
                main_time = t[i]
            A_drag = (np.pi * (rocket.D_rocket / 2) ** 2) * rocket.Cd + (np.pi * D_drogue ** 2) * 0.25 * Cd_drogue + \
                     (np.pi * D_main ** 2) * 0.25 * Cd_main
        elif apogee_time >= 0 and t[i] >= apogee_time + drogue_time:
            A_drag = (np.pi * (rocket.D_rocket / 2) ** 2) * rocket.Cd + (np.pi * D_drogue ** 2) * 0.25 * Cd_drogue
        else:
            A_drag = (np.pi * rocket.D_rocket ** 2) * rocket.Cd * 0.25

        D = (A_drag * rho_air) * 0.5

        p1, l1 = ballistics_ode(y[i], v[i], T[i], D, m_vehicle[i], g)
        p2, l2 = ballistics_ode(y[i] + 0.5 * p1 * dt, v[i] + 0.5 * l1 * dt, T[i], D, m_vehicle[i], g)
        p3, l3 = ballistics_ode(y[i] + 0.5 * p2 * dt, v[i] + 0.5 * l2 * dt, T[i], D, m_vehicle[i], g)
        p4, l4 = ballistics_ode(y[i] + 0.5 * p3 * dt, v[i] + 0.5 * l3 * dt, T[i], D, m_vehicle[i], g)

        y = np.append(y, y[i] + (1 / 6) * (p1 + 2 * (p2 + p3) + p4) * dt)
        v = np.append(v, v[i] + (1 / 6) * (l1 + 2 * (l2 + l3) + l4) * dt)
        acc = np.append(acc, (1 / 6) * (l1 + 2 * (l2 + l3) + l4))

        Mach = np.append(Mach, v[i] / atm.ATMOSPHERE_1976(y[i]).v_sonic)

        if y[i + 1] <= y[i] and m_prop[i] == 0 and apogee == 0:
            apogee = y[i]
            apogee_time = t[np.where(y == apogee)]

        i += 1

    if y[- 1] < 0:
        y = np.delete(y, - 1)
        v = np.delete(v, - 1)
        acc = np.delete(acc, - 1)
        t = np.delete(t, - 1)

    v_rail = v[np.where(y >= rail_length)]
    v_rail = v_rail[0]
    y_burnout = y[np.where(v == np.max(v))]
    y_burnout = y_burnout[0]

    I_total, I_sp = get_impulses(np.mean(T), t, m_prop)

    ballistics = Ballistics(t, y, v, a, v_rail, y_burnout, Mach)
    # ib_parameters = InternalBallistics(t, P0, F, I_total, I_sp, t_burnout, n_cf, E_opt, V_prop_CP, A_burn_CP, Kn,
    #                                    m_prop, grain_mass_flux, optimal_grain_length, initial_port_to_throat,
    #                                    burn_profile, V_empty, initial_to_final_kn)

    return P0


def get_burn_area(grain, x: float, j: int):
    """ Calculates the BATES burn area given the web distance and segment number. """
    N, D_grain, D_core, L_grain = grain.N, grain.D_grain, grain.D_core, grain.L_grain
    Ab = np.pi * (((D_grain ** 2) - (D_core[j] + 2 * x) ** 2) / 2 + (L_grain[j] - 2 * x) * (D_core[j] + 2 * x))
    return Ab


def get_propellant_volume(grain, x: float, j: int):
    """ Calculates the BATES grain volume given the web distance and segment number. """
    N, D_grain, D_core, L_grain = grain.N, grain.D_grain, grain.D_core, grain.L_grain
    Vp = (np.pi / 4) * (((D_grain ** 2) - ((D_core[j] + 2 * x) ** 2)) * (L_grain[j] - 2 * x))
    return Vp


def ballistics_ode(y, v, T, D, M, g):
    """ Returns dydt and dvdt. """
    if v < 0:
        x = -1
    else:
        x = 1
    dvdt = (T - x * D * (v ** 2)) / M - g
    dydt = v
    return dydt, dvdt
