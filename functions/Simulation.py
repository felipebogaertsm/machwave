import numpy as np

from functions.Propellant import *
from functions.InternalBallistics import *


def run_simulation(prop, propellant, grain, structure, dt, P_igniter, P_ext):
    # Initial conditions:
    web = np.array([0])
    t = np.array([0])
    P0, P0_psi, P_exit = np.array([P_igniter]), np.array([P_igniter]) * 1.45e-4, np.array([P_ext])

    r = np.array([])
    V0 = np.array([])
    Exp_opt = np.array([])
    A_burn, V_prop = np.array([]), np.array([])
    m_prop = np.array([])
    n_kin, n_bl, n_tp, n_cf = np.array([]), np.array([]), np.array([]), np.array([])
    C_f, T = np.array([]), np.array([])
    critical_pressure_ratio = (2 / (propellant.k_mix_ch + 1)) ** (propellant.k_mix_ch /
                                                                  (propellant.k_mix_ch - 1))

    V_empty = np.pi * structure.L_chamber * (structure.D_chamber ** 2) / 4

    i = 0
    while P0[i] >= P_ext / critical_pressure_ratio:

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
        t = np.append(t, t[i] + dt)

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

        i += 1

    I_total, I_sp = get_impulses(np.mean(T), t, m_prop)

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
