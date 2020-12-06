import numpy as np
import scipy.optimize

from functions.Propellant import *


# Internal Ballistic related functions:


class InternalBallistics:
    def __init__(self, t, P0, T, T_mean, I_total, I_sp, t_burnout, t_thrust, nozzle_eff, E_opt, V_prop_CP, A_burn_CP,
                 Kn, m_prop, grain_mass_flux, optimal_grain_length, initial_port_to_throat, burn_profile, V_empty,
                 initial_to_final_kn):
        self.t = t
        self.P0 = P0
        self.T = T
        self.T_mean = T_mean
        self.I_total = I_total
        self.I_sp = I_sp
        self.t_burnout = t_burnout
        self.t_thrust = t_thrust
        self.nozzle_eff = nozzle_eff
        self.E_opt = E_opt
        self.V_prop = V_prop_CP
        self.A_burn = A_burn_CP
        self.Kn = Kn
        self.m_prop = m_prop
        self.grain_mass_flux = grain_mass_flux
        self.optimal_grain_length = optimal_grain_length
        self.initial_port_to_throat = initial_port_to_throat
        self.burn_profile = burn_profile
        self.V_empty = V_empty
        self.initial_to_final_kn = initial_to_final_kn


class BATES:
    def __init__(self, wr: int, N: int, D_grain: float, D_core: np.array, L_grain: np.array):
        self.wr = wr
        self.N = N
        self.D_grain = D_grain
        self.D_core = D_core
        self.L_grain = L_grain

    def get_optimal_segment_length(self):
        """ Returns the optimal length for each of the input grains. """
        optimal_grain_length = 1e3 * 0.5 * (3 * self.D_grain + self.D_core)
        return optimal_grain_length

    def get_mass_flux_per_segment(self, grain, r: float, pp, x):
        """ Returns a numpy multidimensional array with the mass flux for each grain. """
        segment_mass_flux = np.zeros((self.N, np.size(x)))
        segment_mass_flux = np.zeros((self.N, np.size(x)))
        total_grain_Ab = np.zeros((self.N, np.size(x)))
        for j in range(self.N):
            for i in range(np.size(r)):
                for k in range(j + 1):
                    total_grain_Ab[j, i] = total_grain_Ab[j, i] + get_burn_area(grain, x[i], k)
                segment_mass_flux[j, i] = (total_grain_Ab[j, i] * pp * r[i])
                segment_mass_flux[j, i] = (segment_mass_flux[j, i]) / get_circle_area(self.D_core[j] + x[i])
        return segment_mass_flux


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


def get_critical_pressure(k_mix_ch):
    """Returns value of the critical pressure ratio. """
    return (2 / (k_mix_ch + 1)) ** (k_mix_ch / (k_mix_ch - 1))


def solve_cp_seidel(P0: float, Pe: float, Ab: float, V0: float, At: float, pp: float,
                    k: float, R: float, T0: float, r: float):
    """ Calculates the chamber pressure by solving Hans Seidel's differential equation. """
    P_critical_ratio = (2 / (k + 1)) ** (k / (k - 1))
    if Pe / P0 <= P_critical_ratio:
        H = ((k / (k + 1)) ** 0.5) * ((2 / (k + 1)) ** (1 / (k - 1)))
    else:
        H = ((Pe / P0) ** (1 / k)) * \
            (((k / (k - 1)) * (1 - (Pe / P0) ** ((k - 1) / k))) ** 0.5)
    dP0dt = ((R * T0 * Ab * pp * r) -
             (P0 * At * H * ((2 * R * T0) ** 0.5))) / V0
    return dP0dt


def get_opt_expansion_ratio(k, P0, P_ext):
    Exp_opt = ((((k + 1) / 2) ** (1 / (k - 1))) * ((P_ext / P0) ** (1 / k)) *
               np.sqrt(((k + 1) / (k - 1)) * (1 - (P_ext / P0) ** ((k - 1) / k)))) ** - 1
    return Exp_opt


def get_exit_mach(k: float, E: float):
    """ Gets the exit Mach number of the nozzle flow. """
    M_exit = scipy.optimize.fsolve(
        lambda x: (((1 + 0.5 * (k - 1) * x ** 2) / (1 + 0.5 * (k - 1))) ** ((k + 1) / (2 * (k - 1)))) / x - E,
        [10]
    )
    return M_exit[0]


def get_exit_pressure(k_2ph_ex, E, P0):
    """ Returns the exit pressure of the nozzle flow. """
    Mach_exit = get_exit_mach(k_2ph_ex, E)
    P_exit = P0 * (1 + 0.5 * (k_2ph_ex - 1) * Mach_exit ** 2) ** (- k_2ph_ex / (k_2ph_ex - 1))
    return P_exit


def get_circle_area(diameter: float):
    """ Returns the area of the circle based on circle diameter. """
    Area = np.pi * 0.25 * diameter ** 2
    return Area


def get_thrust_coeff(P0, P_exit, P_external, E, k_2ph_ex, n_cf):
    """ Returns value for thrust coefficient based on the chamber pressure and correction factor. """
    P_exit = P_external
    Pr = P_external / P0
    Cf_ideal = np.sqrt(((2 * k_2ph_ex ** 2) / (k_2ph_ex - 1)) *
                       ((2 / (k_2ph_ex + 1)) ** ((k_2ph_ex + 1) / (k_2ph_ex - 1))) * (1 - Pr **
                                                                                      ((k_2ph_ex - 1) / k_2ph_ex)))
    Cf = (Cf_ideal - E * (P_exit - P_external) / P0) * n_cf
    return Cf, Cf_ideal


def get_impulses(F_avg, t, t_burnout, m_prop):
    """ Returns total and specific impulse, given the average thrust, time nparray and propellant mass nparray. """
    t = t[t <= t_burnout]
    index = np.where(t == t_burnout)
    m_prop = m_prop[: index[0][0]]
    I_total = F_avg * t[-1]
    I_sp = I_total / (m_prop[0] * 9.81)
    return I_total, I_sp


def get_burn_profile(A_burn: list):
    """ Returns string with burn profile. """
    if A_burn[0] / A_burn[-1] > 1.02:
        burn_profile = 'Regressive'
    elif A_burn[0] / A_burn[-1] < 0.98:
        burn_profile = 'Progressive'
    else:
        burn_profile = 'Neutral'
    return burn_profile


def get_operational_correction_factors(P0, P_external, P0_psi, propellant, structure, critical_pressure_ratio, V0, t):
    """ Returns kinetic, two-phase and boundary layer correction factors based on a015140. """
    C7, termC2, E_cf = 0, 0, 0
    n_cf, n_kin, n_bl, n_tp = 0, 0, 0, 0

    # Kinetic losses
    if P0_psi >= 200:
        n_kin = 33.3 * 200 * (propellant.Isp_frozen / propellant.Isp_shifting) / P0_psi
    else:
        n_kin = 0

    # Boundary layer and two phase flow losses
    if P_external / P0 <= critical_pressure_ratio:

        termC2 = 1 + 2 * np.exp(- structure.C2 * P0_psi ** 0.8 * t / ((structure.D_throat / 0.0254) ** 0.2))
        E_cf = 1 + 0.016 * structure.Exp_ratio ** -9
        n_bl = structure.C1 * ((P0_psi ** 0.8) / ((structure.D_throat / 0.0254) ** 0.2)) * termC2 * E_cf

        C7 = 0.454 * (P0_psi ** 0.33) * (propellant.qsi_ch ** 0.33) * (1 - np.exp(-0.004 * (V0 / get_circle_area(
            structure.D_throat)) / 0.0254) * (1 + 0.045 * structure.D_throat / 0.0254))
        if 1 / propellant.M_ch >= 0.9:
            C4 = 0.5
            if structure.D_throat / 0.0254 < 1:
                C3, C5, C6 = 9, 1, 1
            elif 1 <= structure.D_throat / 0.0254 < 2:
                C3, C5, C6 = 9, 1, 0.8
            elif structure.D_throat / 0.0254 >= 2:
                if C7 < 4:
                    C3, C5, C6 = 13.4, 0.8, 0.8
                elif 4 <= C7 <= 8:
                    C3, C5, C6 = 10.2, 0.8, 0.4
                elif C7 > 8:
                    C3, C5, C6 = 7.58, 0.8, 0.33
        elif 1 / propellant.M_ch < 0.9:
            C4 = 1
            if structure.D_throat / 0.0245 < 1:
                C3, C5, C6 = 44.5, 0.8, 0.8
            elif 1 <= structure.D_throat / 0.0254 < 2:
                C3, C5, C6 = 30.4, 0.8, 0.4
            elif structure.D_throat / 0.0254 >= 2:
                if C7 < 4:
                    C3, C5, C6 = 44.5, 0.8, 0.8
                elif 4 <= C7 <= 8:
                    C3, C5, C6 = 30.4, 0.8, 0.4
                elif C7 > 8:
                    C3, C5, C6 = 25.2, 0.8, 0.33
        n_tp = C3 * ((propellant.qsi_ch * C4 * C7 ** C5) / (P0_psi ** 0.15 * structure.Exp_ratio ** 0.08 *
                                                            (structure.D_throat / 0.0254) ** C6))
    else:
        n_tp = 0
        n_bl = 0

    return n_kin, n_tp, n_bl


def get_expansion_ratio(Pe: float, P0: list, k: float, critical_pressure_ratio: float):
    """ Returns array of the optimal expansion ratio for each pressure ratio. """
    E = np.zeros(np.size(P0))

    for i in range(np.size(P0)):
        if Pe / P0[i] <= critical_pressure_ratio:
            pressure_ratio = Pe / P0[i]
            E[i] = (((k + 1) / 2) ** (1 / (k - 1)) * pressure_ratio ** (1 / k) * (
                    (k + 1) / (k - 1) * (1 - pressure_ratio ** ((k - 1) / k))) ** 0.5) ** -1
        else:
            E[i] = 1
    return np.mean(E)
