# This file contains most of the calculations of the internal ballistic and trajectory. This includes the main loop of
# the program, which contains the calculations of the differential equations and several other important parameters.

import fluids.atmosphere as atm

from functions.InternalBallistics import *
from functions.Ballistics import *


def run_ballistics(prop, propellant, grain, structure, rocket, recovery, dt, ddt, h0, P_igniter, rail_length):
    # Initial conditions:
    web = np.array([0])
    t = np.array([0])
    P_ext, rho_air, g = np.array([]), np.array([]), np.array([])
    P0, P0_psi, P_exit = np.array([P_igniter]), np.array([P_igniter]) * 1.45e-4, np.array([])
    y, v = np.array([0]), np.array([0])
    Mach = np.array([0])

    # Allocating numpy arrays for future calculations:
    # Total mass of the vehicle:
    m_vehicle = np.array([])
    # Burn rate:
    r = np.array([])
    # Chamber empty volume:
    V0 = np.array([])
    # Optimal expansion ratio:
    Exp_opt = np.array([])
    # Burn area and propellant volume:
    A_burn, V_prop = np.array([]), np.array([])
    # Propellant mass:
    m_prop = np.array([])
    # Thrust coefficient correction factors:
    n_kin, n_bl, n_tp, n_cf = np.array([]), np.array([]), np.array([]), np.array([])
    # Thrust coefficient and thrust:
    Cf, Cf_ideal, T = np.array([]), np.array([]), np.array([])

    # Pre calculations:
    # Critical pressure ratio:
    critical_pressure_ratio = (2 / (propellant.k_mix_ch + 1)) ** (propellant.k_mix_ch /
                                                                  (propellant.k_mix_ch - 1))
    # Divergent correction factor:
    n_div = 0.5 * (1 + np.cos(np.deg2rad(structure.Div_angle)))
    # Variables used to store the apogee, apogee time and main chute ejection time:
    apogee, apogee_time, main_time = 0, - 1, 0
    # Calculation of the empty chamber volume (constant throughout the operation):
    V_empty = np.pi * structure.L_chamber * (structure.D_chamber ** 2) / 4

    # Is the propellant mass is non zero, 'end_thrust' must be False, since there is still thrust being produced.
    # After the propellant is finished burning and the thrust chamber has stopped producing supersonic flow,
    # 'end_thrust' is changed to a True value and the internal ballistics section of the while loop below stops running.
    end_thrust = False
    end_burn = False
    i = 0
    while y[i] >= 0 or m_prop[i - 1] > 0:

        t = np.append(t, t[i] + dt)

        # Obtaining the value for the air density and the acceleration of gravity in function of the current altitude.
        rho_air = np.append(rho_air, atm.ATMOSPHERE_1976(y[i] + h0).rho)
        g = np.append(g, atm.ATMOSPHERE_1976.gravity(h0 + y[i]))
        P_ext = np.append(P_ext, atm.ATMOSPHERE_1976(h0 + y[i]).P)

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

            k1 = solve_cp_seidel(P0[i], P_ext[i], A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
            k2 = solve_cp_seidel(P0[i] + 0.5 * k1 * dt, P_ext[i], A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
            k3 = solve_cp_seidel(P0[i] + 0.5 * k2 * dt, P_ext[i], A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
            k4 = solve_cp_seidel(P0[i] + 0.5 * k3 * dt, P_ext[i], A_burn[i], V0[i], structure.A_throat, propellant.pp,
                                 propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])

            P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)
            P0_psi = np.append(P0_psi, P0[i] * 1.45e-4)

            Exp_opt = np.append(Exp_opt, get_opt_expansion_ratio(propellant.k_2ph_ex, P0[i], P_ext[i]))
            P_exit = np.append(P_exit, get_exit_pressure(propellant.k_2ph_ex, structure.Exp_ratio, P0[i]))
            n_kin_atual, n_tp_atual, n_bl_atual = get_operational_correction_factors(P0[i], P_ext[i], P0_psi[i],
                                                                                     propellant, structure,
                                                                                     critical_pressure_ratio, V0[0],
                                                                                     t[i])
            n_kin, n_tp, n_bl = np.append(n_kin, n_kin_atual), np.append(n_tp, n_tp_atual), np.append(n_bl, n_bl_atual)
            n_cf = np.append(n_cf, ((100 - (n_kin_atual + n_bl_atual + n_tp_atual)) * n_div / 100 * propellant.n_ce))

            Cf_atual, Cf_ideal_atual = get_thrust_coeff(P0[i], P_exit[i], P_ext[i], structure.Exp_ratio,
                                                        propellant.k_2ph_ex, n_cf[i])
            Cf, Cf_ideal = np.append(Cf, Cf_atual), np.append(Cf_ideal, Cf_ideal_atual)
            T = np.append(T, Cf[i] * structure.A_throat * P0[i])

            if m_prop[i] == 0 and end_burn is False:
                t_burnout = t[i]
                end_burn = True

            # This if statement changes 'end_thrust' to True if supersonic flow is not achieved anymore.
            if P0[i] <= P_ext[i] / critical_pressure_ratio:
                t_thrust = t[i]
                dt = dt * ddt
                T_mean = np.mean(T)
                end_thrust = True

        # This else statement is necessary since the thrust and propellant mass arrays are still being used inside the
        # main while loop. Therefore, it is necessary to append 0 to these arrays for the ballistic part of the while
        # loop to work correctly.
        else:
            m_prop = np.append(m_prop, 0)
            T = np.append(T, 0)

        # Entering first value for the vehicle mass and acceleration:
        if i == 0:
            m_vehicle_initial = m_prop[0] + rocket.mass_wo_motor + structure.m_motor
            m_vehicle = np.append(m_vehicle, m_vehicle_initial)
            acc = np.array([T[0] / (rocket.mass_wo_motor + structure.m_motor + m_prop[0])])

        # Appending the current vehicle mass, consisting of the motor structural mass, mass without the motor and
        # propellant mass.
        m_vehicle = np.append(m_vehicle, m_prop[i] + structure.m_motor + rocket.mass_wo_motor)

        # Drag properties:
        if v[i] < 0 and y[i] <= recovery.main_chute_activation_height and m_prop[i] == 0:
            if main_time == 0:
                main_time = t[i]
            A_drag = (np.pi * (rocket.D_rocket / 2) ** 2) * rocket.Cd + (np.pi * recovery.D_drogue ** 2) * 0.25 * \
                recovery.Cd_drogue + (np.pi * recovery.D_main ** 2) * 0.25 * recovery.Cd_main
        elif apogee_time >= 0 and t[i] >= apogee_time + recovery.drogue_time:
            A_drag = (np.pi * (rocket.D_rocket / 2) ** 2) * rocket.Cd + (np.pi * recovery.D_drogue ** 2) * 0.25 * \
                     recovery.Cd_drogue
        else:
            A_drag = (np.pi * rocket.D_rocket ** 2) * rocket.Cd * 0.25

        D = (A_drag * rho_air[i]) * 0.5

        p1, l1 = ballistics_ode(y[i], v[i], T[i], D, m_vehicle[i], g[i])
        p2, l2 = ballistics_ode(y[i] + 0.5 * p1 * dt, v[i] + 0.5 * l1 * dt, T[i], D, m_vehicle[i], g[i])
        p3, l3 = ballistics_ode(y[i] + 0.5 * p2 * dt, v[i] + 0.5 * l2 * dt, T[i], D, m_vehicle[i], g[i])
        p4, l4 = ballistics_ode(y[i] + 0.5 * p3 * dt, v[i] + 0.5 * l3 * dt, T[i], D, m_vehicle[i], g[i])

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
    flight_time = t[- 1]

    nozzle_eff = Cf / Cf_ideal

    I_total, I_sp = get_impulses(T_mean, t, t_burnout, m_prop)

    ballistics = Ballistics(t, y, v, acc, v_rail, y_burnout, Mach, apogee_time[0], flight_time, P_ext)
    optimal_grain_length = grain.get_optimal_segment_length()
    initial_port_to_throat = (grain.D_core[- 1] ** 2) / (structure.D_throat ** 2)
    burn_profile = get_burn_profile(A_burn[A_burn != 0.0])
    Kn = A_burn / structure.A_throat
    Kn_non_zero = Kn[Kn != 0.0]
    initial_to_final_kn = Kn_non_zero[0] / Kn_non_zero[- 1]
    grain_mass_flux = grain.get_mass_flux_per_segment(grain, r, propellant.pp, web)
    ib_parameters = InternalBallistics(t, P0, T, T_mean, I_total, I_sp, t_burnout, t_thrust, nozzle_eff, Exp_opt,
                                       V_prop, A_burn, Kn, m_prop, grain_mass_flux, optimal_grain_length,
                                       initial_port_to_throat, burn_profile, V_empty, initial_to_final_kn, P_exit)

    return ballistics, ib_parameters


def ballistics_ode(y, v, T, D, M, g):
    """ Returns dydt and dvdt. """
    if v < 0:
        x = -1
    else:
        x = 1
    dvdt = (T - x * D * (v ** 2)) / M - g
    dydt = v
    return dydt, dvdt
