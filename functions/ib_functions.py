import numpy as np
import scipy.optimize

from functions.propellant import *


# Internal Ballistic related functions:


class IBParameters:
    def __init__(self, t, P0, F, I_total, I_sp, t_burnout, n_cf, E, V_prop_CP, A_burn_CP, Kn, m_prop, grain_mass_flux,
                 optimal_grain_length, initial_port_to_throat, burn_profile, V_empty, initial_to_final_kn):
        self.t = t
        self.P0 = P0
        self.F = F
        self.I_total = I_total
        self.I_sp = I_sp
        self.t_burnout = t_burnout
        self.n_cf = n_cf
        self.E = E
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

    def get_min_core_diameter_index(self):
        """ Finds the smallest core diameter and its index 'j'. """
        N, D_core = self.N, self.D_core
        D_core_min = np.amin(D_core)
        # If there is more than one one index where the initial core diameter is minimal, the for loop
        # only returns the first index where it happens.
        for j in range(N):
            if D_core[j] == D_core_min:
                D_core_min_index = j
                break
        return D_core_min_index

    def get_burn_area(self, x: float, j: int):
        """ Calculates the BATES burn area given the web distance and segment number. """
        N, D_grain, D_core, L_grain = self.N, self.D_grain, self.D_core, self.L_grain
        Ab = np.pi * (((D_grain ** 2) - (D_core[j] + 2 * x) ** 2) / 2 + (L_grain[j] - 2 * x) *
                      (D_core[j] + 2 * x))
        return Ab

    def get_propellant_volume(self, x: float, j: int):
        """ Calculates the BATES grain volume given the web distance and segment number. """
        N, D_grain, D_core, L_grain = self.N, self.D_grain, self.D_core, self.L_grain
        Vp = (np.pi / 4) * (((D_grain ** 2) -
                             ((D_core[j] + 2 * x) ** 2)) * (L_grain[j] - 2 * x))
        return Vp

    def get_web_array(self):
        """ Returns the web thickness array for each grain. """

        # Finding the getWebArray thickness of each individual grain. The j index refers to the grain segment and i
        # refers to the getWebArray step (number of steps set by 'wr').
        wr, N, D_grain, D_core, L_grain = self.wr, self.N, self.D_grain, self.D_core, self.L_grain
        w = np.zeros((N, wr))
        for j in range(N):
            if 0.5 * (D_grain - D_core[j]) > L_grain[j]:
                w[j] = np.linspace(0, (L_grain[j] / 2), wr)
            elif 0.5 * (D_grain - D_core[j]) <= L_grain[j]:
                w[j] = np.linspace(0, 0.5 * (D_grain - D_core[j]), wr)
        return w

    def get_optimal_segment_length(self):
        """ Returns the optimal length for each of the input grains. """
        optimal_grain_length = 1e3 * 0.5 * (3 * self.D_grain + self.D_core)
        return optimal_grain_length

    def get_mass_flux_per_segment(self, r: float, pp, x):
        """ Returns a numpy multidimensional array with the mass flux for each grain. """
        segment_mass_flux = np.zeros((self.N, np.size(x)))
        segment_mass_flux = np.zeros((self.N, np.size(x)))
        total_grain_Ab = np.zeros((self.N, np.size(x)))
        for j in range(self.N):
            for i in range(np.size(r)):
                for k in range(j + 1):
                    # print(j, i, k)
                    total_grain_Ab[j, i] = total_grain_Ab[j,
                                                          i] + self.get_burn_area(x[i], k)
                segment_mass_flux[j, i] = (total_grain_Ab[j, i] * pp * r[i])
                segment_mass_flux[j, i] = (
                                              segment_mass_flux[j, i]) / get_circle_area(self.D_core[j] + x[i])
        return segment_mass_flux


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


def get_exit_mach(k: float, E: float):
    """ Gets the exit Mach number of the nozzle flow. """
    E = np.mean(E)
    M_exit = scipy.optimize.fsolve(
        lambda x: (((1 + 0.5 * (k - 1) * x ** 2) / (1 + 0.5 * (k - 1)))
                   ** ((k + 1) / (2 * (k - 1)))) / x - E,
        [10]
    )
    return M_exit[0]


def get_exit_pressure(k_2ph_ex, E, P0):
    """ Returns the exit pressure of the nozzle flow. """
    P_exit = np.zeros(np.size(P0))
    Mach_exit = get_exit_mach(k_2ph_ex, E)
    for i in range(np.size(P0)):
        P_exit[i] = P0[i] * (1 + 0.5 * (k_2ph_ex - 1) *
                             Mach_exit ** 2) ** (- k_2ph_ex / (k_2ph_ex - 1))
    return P_exit


def get_circle_area(diameter: float):
    """ Returns the area of the circle based on circle diameter. """
    Area = np.pi * 0.25 * diameter ** 2
    return Area


def get_chamber_volume(L_cc: float, D_in: float, V_prop: np.array):
    """ Returns the instant and empty chamber volume for each getWebArray distance value. """
    V_empty = np.pi * L_cc * (D_in ** 2) / 4
    V0 = V_empty - V_prop
    return V0, V_empty


def get_thrust_coefficient(P0, P_external, P_exit, E, k_2ph_ex, n_cf):
    """ Returns value for thrust coefficient based on the chamber pressure and correction factor. """
    Pr = P_external / P0
    Cf_ideal = np.sqrt(
        ((2 * k_2ph_ex ** 2) / (k_2ph_ex - 1)) * ((2 / (k_2ph_ex + 1)) **
                                                  ((k_2ph_ex + 1) / (k_2ph_ex - 1))) *
        (1 - Pr ** ((k_2ph_ex - 1) / k_2ph_ex)))
    Cf = (Cf_ideal - E * (P_exit - P_external) / P0) * n_cf
    return Cf


def get_impulses(F_avg, t, m_prop):
    """ Returns total and specific impulse, given the average thrust, time nparray and prop mass nparray. """
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


def get_operational_correction_factors(P0: list, Pe: float, P0psi: list, Isp_frozen: float, Isp_shifting: float,
                                       E: float, Dt: float, qsi: float, index: int, critical_pressure_ratio: float,
                                       C1: float, C2: float, V0: float, M: float, t: list):
    """ Returns kinetic, two-phase and boundary layer correction factors based on a015140. """
    C7, termC2, E_cf = np.zeros(index), np.zeros(index), np.zeros(index)
    n_cf, n_kin, n_bl, n_tp = np.zeros(index), np.zeros(
        index), np.zeros(index), np.zeros(index)

    for i in range(index):

        # Kinetic losses
        if P0psi[i] >= 200:
            n_kin[i] = 33.3 * 200 * (Isp_frozen / Isp_shifting) / P0psi[i]
        else:
            n_kin[i] = 0

        # Boundary layer and two phase flow losses
        if Pe / P0[i] <= critical_pressure_ratio:

            termC2[i] = 1 + 2 * np.exp(-C2 * (P0psi[i])
                                       ** 0.8 * t[i] / ((Dt / 0.0254) ** 0.2))
            E_cf[i] = 1 + 0.016 * E ** -9
            n_bl[i] = C1 * ((P0psi[i] ** 0.8) / ((Dt / 0.0254)
                                                 ** 0.2)) * (termC2[i]) * E_cf[i]

            C7[i] = 0.454 * (P0psi[i] ** 0.33) * (qsi ** 0.33) * (
                    1 - np.exp(-0.004 * (V0[1] / get_circle_area(Dt)) / 0.0254) * (1 + 0.045 * Dt / 0.0254))
            if 1 / M >= 0.9:
                C4 = 0.5
                if Dt / 0.0254 < 1:
                    C3, C5, C6 = 9, 1, 1
                elif 1 <= Dt / 0.0254 < 2:
                    C3, C5, C6 = 9, 1, 0.8
                elif Dt / 0.0254 >= 2:
                    if C7[i] < 4:
                        C3, C5, C6 = 13.4, 0.8, 0.8
                    elif 4 <= C7[i] <= 8:
                        C3, C5, C6 = 10.2, 0.8, 0.4
                    elif C7[i] > 8:
                        C3, C5, C6 = 7.58, 0.8, 0.33
            elif 1 / M < 0.9:
                C4 = 1
                if Dt / 0.0245 < 1:
                    C3, C5, C6 = 44.5, 0.8, 0.8
                elif 1 <= Dt / 0.0254 < 2:
                    C3, C5, C6 = 30.4, 0.8, 0.4
                elif Dt / 0.0254 >= 2:
                    if C7[i] < 4:
                        C3, C5, C6 = 44.5, 0.8, 0.8
                    elif 4 <= C7[i] <= 8:
                        C3, C5, C6 = 30.4, 0.8, 0.4
                    elif C7[i] > 8:
                        C3, C5, C6 = 25.2, 0.8, 0.33
            n_tp[i] = C3 * ((qsi * C4 * C7[i] ** C5) / (P0psi[i] ** 0.15 * E ** 0.08 *
                                                        (Dt / 0.0254) ** C6))
        else:
            n_tp[i] = 0
            n_bl[i] = 0
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


def run_internal_ballistics(propellant, grain, structure, web_res, P_igniter, P_external, dt, prop):
    # BURN REGRESSION:

    # Creating a web distance array, for each grain:
    web = grain.get_web_array()

    # Pre-allocating the burn area and volume matrix for each grain segment. Rows are the grain segment number and
    # columns are the burn area or volume value for each web regression step.

    A_burn_segment = np.zeros((grain.N, web_res))
    V_propellant_segment = np.zeros((grain.N, web_res))

    for j in range(grain.N):
        for i in range(web_res):
            A_burn_segment[j, i] = grain.get_burn_area(web[j, i], j)
            V_propellant_segment[j, i] = grain.get_propellant_volume(web[j, i], j)

    # In case there are different initial core diameters or grain lengths, the for loop below interpolates all the burn
    # area and Propellant volume data in respect to the largest web thickness of the motor.
    # This ensures that that all grains ignite at the same time in the simulation and also that the distance between
    # steps is equal for all grains in the matrix A_burn_segment and V_propellant_segment.

    D_core_min_index = grain.get_min_core_diameter_index()
    for j in range(grain.N):
        A_burn_segment[j, :] = np.interp(web[D_core_min_index, :], web[j, :],
                                         A_burn_segment[j, :], left=0, right=0)
        V_propellant_segment[j, :] = np.interp(web[D_core_min_index, :], web[j, :],
                                               V_propellant_segment[j, :], left=0, right=0)

    # Adding the columns of the matrices A_burn_segment and V_propellant_segment to generate the vectors A_burn and
    # V_prop, that contain the sum of the data for all grains in function of the web steps:
    A_burn = A_burn_segment.sum(axis=0)
    V_prop = V_propellant_segment.sum(axis=0)

    # Setting the web thickness matrix to the largest web thickness vector:
    web = web[D_core_min_index, :]

    # Core area:
    A_core = np.array([])
    for j in range(grain.N):
        A_core = np.append(A_core, get_circle_area(grain.D_core[j]))
    # Port area:
    A_port = A_core[-1]
    # Port to throat area ratio:
    initial_port_to_throat = A_port / structure.A_throat

    # Getting the burn profile
    burn_profile = get_burn_profile(A_burn)
    # Getting the optimal length for each grain segment
    optimal_grain_length = grain.get_optimal_segment_length()

    # Finding the initial to final Kn ratio:
    non_zero_A_burn = A_burn[np.nonzero(A_burn)]
    initial_to_final_kn = A_burn[0] / non_zero_A_burn[-1]

    # CHAMBER PRESSURE RK4 SOLVER:

    # Calculating the free chamber volume for each web step:
    V0, V_empty = get_chamber_volume(structure.L_chamber, structure.D_chamber, V_prop)

    # Critical pressure (isentropic supersonic flow):
    critical_pressure_ratio = get_critical_pressure(propellant.k_mix_ch)

    # Initial conditions:
    P0, x, t, t_burnout = np.array([P_igniter]), np.array([0]), np.array([0]), 0
    # Declaring arrays:
    r0, re, r = np.array([]), np.array([]), np.array([])

    # While loop iterates until the new instant web thickness vector 'x' is larger than the web thickness (last
    # element of vector 'w') or the internal chamber pressure is smaller than critical pressure (making the nozzle
    # exhaust subsonic).
    i = 0
    while x[i] <= web[web_res - 1] or P0[i] >= P_external / critical_pressure_ratio:
        # burn_rate_coefs selects value for a and n that suits the current chamber pressure of the iteration step.
        a, n = get_burn_rate_coefs(prop, P0[i])
        # if 'a' and 'n' are negative, exit the program (lacking burn rate data for the current iteration of P0).
        if a < 0:
            exit()
        # The first time the while loop operates, the values for the burn rate are declared and written based on the
        # initial igniter pressure. 'r0' stands for the non-erosive burn rate term and 'r' stands for the total burn
        # rate. Currently, the program does not support erosive burning yet, o 'r0 = r'. 'r0' is calculated using St.
        # Robert's Burn Rate Law.
        r0 = np.append(r0, (a * (P0[i] * 1e-6) ** n) * 1e-3)
        re = np.append(re, 0)
        r = np.append(r, r0[i] + re[i])
        # The web distance that the combustion consumes on each time step 'dt' is represented by 'dx':
        dx = dt * r[i]
        # The instant web distance vector is appended with latest 'dx' value:
        x = np.append(x, x[i] + dx)
        # The time vector 't' is also modified and the time step 'dt' is added to the last 't[i]' value:
        t = np.append(t, t[i] + dt)
        # In order for the burn area, chamber volume and Propellant volume vectors to be in function of time ('t') or in
        # function of web distance ('x') the old vectors 'A_burn', 'V0' and 'V_prop' must be interpolated from the old
        # set of web thickness data 'w' to the new vector 'x'.
        # A_burn_CP is the interpolated value for A_burn, in function of x and t;
        # V0_CP is the interpolated value for V0, in function of x and t;
        # V_prop_CP is the interpolated value for V_prop, in function of x and t.
        A_burn_CP = np.interp(x, web, A_burn, left=0, right=0)
        V0_CP = np.interp(x, web, V0, right=V_empty)
        V_prop_CP = np.interp(x, web, V_prop, right=0)
        # The values above are then used to solve the differential equation by the Range-Kutta 4th order method.
        k1 = solve_cp_seidel(P0[i], P_external, A_burn_CP[i], V0_CP[i], structure.A_throat, propellant.pp,
                             propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
        k2 = solve_cp_seidel(P0[i] + 0.5 * k1 * dt, P_external, A_burn_CP[i], V0_CP[i], structure.A_throat,
                             propellant.pp, propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
        k3 = solve_cp_seidel(P0[i] + 0.5 * k2 * dt, P_external, A_burn_CP[i], V0_CP[i], structure.A_throat,
                             propellant.pp, propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])
        k4 = solve_cp_seidel(P0[i] + 0.5 * k3 * dt, P_external, A_burn_CP[i], V0_CP[i], structure.A_throat,
                             propellant.pp, propellant.k_mix_ch, propellant.R_ch, propellant.T0, r[i])

        P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)
        # 't_burnout' stands for the time on which the Propellant is done burning. If the value for 't_burnout'
        # (declared before the while loop) is 0 and the current iteration of 'AbCP' is also 0, t_burnout is set to the
        # current time value 't[i]'.
        if t_burnout == 0 and A_burn_CP[i] == 0:
            t_burnout = t[i]
        i = i + 1

    # Mass flux per grain:
    grain_mass_flux = grain.get_mass_flux_per_segment(r, propellant.pp, x)
    # Index will be useful to perform next calculations:
    index = np.size(P0)
    # Klemmung calculation:
    Kn = A_burn_CP / structure.A_throat
    # Propellant mass:
    m_prop = V_prop_CP * propellant.pp
    # Conversion of 'P0' from Pa to psi inside a new vector 'P0_psi':
    P0_psi = P0 * 1.45e-4

    # EXPANSION RATIO AND EXIT PRESSURE

    E = get_expansion_ratio(P_external, P0, propellant.k_2ph_ex, get_critical_pressure(propellant.k_mix_ch))
    P_exit = get_exit_pressure(propellant.k_2ph_ex, E, P0)

    # MOTOR PERFORMANCE LOSSES (a015140 paper):

    n_div = 0.5 * (1 + np.cos(np.deg2rad(structure.Div_angle)))
    n_kin, n_tp, n_bl = get_operational_correction_factors(P0, P_external, P0_psi, propellant.Isp_frozen,
                                                           propellant.Isp_shifting, E, structure.D_throat,
                                                           propellant.qsi_ch, index, critical_pressure_ratio,
                                                           structure.C1, structure.C2, V0, propellant.M_ch, t)
    n_cf = ((100 - (n_kin + n_bl + n_tp)) * n_div / 100)

    # THRUST AND IMPULSE:

    Cf = get_thrust_coefficient(P0, P_external, P_exit, E, propellant.k_2ph_ex, n_cf)
    F = Cf * structure.A_throat * P0
    I_total, I_sp = get_impulses(np.mean(F), t, m_prop)

    return IBParameters(t, P0, F, I_total, I_sp, t_burnout, n_cf, E, V_prop_CP, A_burn_CP, Kn, m_prop, grain_mass_flux,
                        optimal_grain_length, initial_port_to_throat, burn_profile, V_empty, initial_to_final_kn)
