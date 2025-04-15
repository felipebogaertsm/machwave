import numpy as np
import scipy.optimize

from machwave.services.math.geometric import get_circle_area


def get_critical_pressure_ratio(k_mix: float) -> float:
    """
    Returns the value of the critical pressure ratio.

    Args:
        k_mix (float): The isentropic exponent of the mixture.

    Returns:
        float: The critical pressure ratio.

    Example:
        critical_ratio = get_critical_pressure_ratio(1.4)
    """
    return (2 / (k_mix + 1)) ** (k_mix / (k_mix - 1))


def get_opt_expansion_ratio(k: float, P_0: float, P_ext: float) -> float:
    """
    Returns the optimal expansion ratio based on the current chamber pressure,
    specific heat ratio, and external pressure.

    Args:
        k (float): The isentropic exponent.
        P_0 (float): The chamber pressure.
        P_ext (float): The external pressure.

    Returns:
        float: The optimal expansion ratio.

    Example:
        expansion_ratio = get_opt_expansion_ratio(1.4, 100000, 10000)
    """
    exp_opt = (
        (((k + 1) / 2) ** (1 / (k - 1)))
        * ((P_ext / P_0) ** (1 / k))
        * np.sqrt(((k + 1) / (k - 1)) * (1 - (P_ext / P_0) ** ((k - 1) / k)))
    ) ** -1

    return exp_opt


def get_exit_mach(k: float, E: float) -> float:
    """
    Calculates the exit Mach number of the nozzle flow.

    Args:
        k (float): The isentropic exponent.
        E (float): The expansion ratio.

    Returns:
        float: The exit Mach number.

    Example:
        exit_mach = get_exit_mach(1.4, 5.0)
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


def get_exit_pressure(k_ex: float, E: float, P_0: float) -> float:
    """
    Calculates the exit pressure of the nozzle flow.

    Args:
        k_ex (float): The isentropic exponent in the exit region.
        E (float): The expansion ratio.
        P_0 (float): The chamber pressure.

    Returns:
        float: The exit pressure.

    Example:
        exit_pressure = get_exit_pressure(1.4, 5.0, 100000)
    """
    Mach_exit = get_exit_mach(k_ex, E)
    P_exit = P_0 * (1 + 0.5 * (k_ex - 1) * Mach_exit**2) ** (-k_ex / (k_ex - 1))
    return P_exit


def get_ideal_thrust_coefficient(
    chamber_pressure: float,
    exit_pressure: float,
    external_pressure: float,
    expansion_ratio: float,
    k_ex: float,
) -> float:
    """
    Calculates the thrust coefficient.

    Source:
    https://www.nakka-rocketry.net/th_thrst.html

    Args:
        chamber_pressure: The chamber pressure (Pa).
        exit_pressure: The exit pressure (Pa).
        external_pressure: The external pressure (Pa).
        expansion_ratio: The expansion ratio.
        k_ex: The isentropic exponent in the exit region.

    Returns:
        The thrust coefficient.

    Example:
        cf_ideal = get_ideal_thrust_coefficient(100e3, 91e3, 90e3, 7.0, 1.4)
    """
    pressure_ratio = exit_pressure / chamber_pressure
    return (
        np.sqrt(
            (2 * (k_ex**2) / (k_ex - 1))
            * ((2 / (k_ex + 1)) ** ((k_ex + 1) / (k_ex - 1)))
            * (1 - (pressure_ratio ** ((k_ex - 1) / k_ex)))
        )
        + expansion_ratio * (exit_pressure - external_pressure) / chamber_pressure
    )


def get_thrust_coefficients(
    P_0: float,
    P_exit: float,
    P_external: float,
    E: float,
    k: float,
    n_cf: float,
) -> tuple[float, float]:
    """
    Calculates the thrust coefficients based on the chamber pressure and correction factor.

    Args:
        P_0 (float): The chamber pressure.
        P_exit (float): The exit pressure.
        P_external (float): The external pressure.
        E (float): The expansion ratio.
        k (float): The isentropic exponent.
        n_cf (float): The correction factor.

    Returns:
        tuple[float, float]: The thrust coefficients (Cf, Cf_ideal).

    Example:
        Cf, Cf_ideal = get_thrust_coefficients(100000, 5000, 1000, 5.0, 1.4, 0.8)
    """
    Cf_ideal = get_ideal_thrust_coefficient(P_0, P_exit, P_external, E, k)
    Cf = Cf_ideal * n_cf

    if Cf <= 0:
        Cf = 0
    if Cf_ideal <= 0:
        Cf_ideal = 0

    return Cf, Cf_ideal


def get_thrust_from_cf(C_f: float, P_0: float, nozzle_throat_area: float) -> float:
    """
    Calculates the thrust based on the thrust coefficient, chamber stagnation pressure,
    and nozzle throat area.

    Args:
        C_f (float): The thrust coefficient.
        P_0 (float): The chamber stagnation pressure.
        nozzle_throat_area (float): The nozzle throat area.

    Returns:
        float: The thrust.

    Example:
        thrust = get_thrust_from_cf(0.8, 100000, 0.02)
    """
    return C_f * P_0 * nozzle_throat_area


def get_thrust_coefficient(
    P_0: float, thrust: float, nozzle_throat_area: float
) -> float:
    """
    Calculates the thrust coefficient based on the chamber stagnation pressure, thrust,
    and nozzle throat area.

    Args:
        P_0 (float): The chamber stagnation pressure.
        thrust (float): The thrust.
        nozzle_throat_area (float): The nozzle throat area.

    Returns:
        float: The thrust coefficient.

    Example:
        Cf = get_thrust_coefficient(100000, 5000, 0.02)
    """
    return thrust / (P_0 * nozzle_throat_area)


def is_flow_choked(
    chamber_pressure: float,
    external_pressure: float,
    critical_pressure_ratio: float,
) -> bool:
    """
    Determines if the flow is choked based on the chamber pressure,
    external pressure, and critical pressure ratio.

    Args:
        chamber_pressure (float): The chamber pressure.
        external_pressure (float): The external pressure.
        critical_pressure_ratio (float): The critical pressure ratio.

    Returns:
        bool: True if the flow is choked, False otherwise.

    Example:
        choked = is_flow_choked(100000, 5000, 0.5)
    """
    return chamber_pressure >= external_pressure / critical_pressure_ratio


def get_total_impulse(average_thrust: float, thrust_time: float) -> float:
    """
    Calculates the total impulse of the operation based on the average thrust and thrust time.

    Args:
        average_thrust (float): The average thrust.
        thrust_time (float): The thrust time.

    Returns:
        float: The total impulse.

    Example:
        total_impulse = get_total_impulse(5000, 3)
    """
    return average_thrust * thrust_time


def get_specific_impulse(total_impulse: float, initial_propellant_mass: float) -> float:
    """
    Calculates the specific impulse of the operation based on the total impulse and initial propellant mass.

    Args:
        total_impulse (float): The total impulse.
        initial_propellant_mass (float): The initial propellant mass.

    Returns:
        float: The specific impulse.

    Example:
        specific_impulse = get_specific_impulse(15000, 100)
    """
    return total_impulse / initial_propellant_mass / 9.81


def get_operational_correction_factors(
    P_0: float,
    P_external: float,
    P_0_psi: float,
    propellant,
    structure,
    critical_pressure_ratio: float,
    V0: float,
    t: float,
) -> tuple[float, float, float]:
    """
    Calculates the kinetic, two-phase, and boundary layer correction factors based
    on A015140.

    Args:
        P_0 (float): The chamber stagnation pressure (Pa).
        P_external (float): The external pressure.
        P_0_psi (float): The chamber pressure in psi.
        propellant: The propellant object.
        structure: The structure object.
        critical_pressure_ratio (float): The critical pressure ratio.
        V0 (float): The free chamber volume.
        t (float): The current time.

    Returns:
        tuple[float, float, float]: The kinetic, two-phase, and boundary layer correction factors.

    Example:
        n_kin, n_tp, n_bl = get_operational_correction_factors(100000, 5000, 100, propellant, structure, 0.5, 0.1, 10)
    """
    C3, C4, C5, C6 = 0, 0, 0, 0

    # Kinetic losses
    if P_0_psi >= 200:
        n_kin = 33.3 * 200 * (propellant.Isp_frozen / propellant.Isp_shifting) / P_0_psi
    else:
        n_kin = 0

    # Boundary layer and two-phase flow losses
    if not is_flow_choked(P_0, P_external, critical_pressure_ratio):
        termc_2 = 1 + 2 * np.exp(
            -structure.nozzle.material.c_2
            * P_0_psi**0.8
            * t
            / ((structure.nozzle.throat_diameter / 0.0254) ** 0.2)
        )
        E_cf = 1 + 0.016 * structure.nozzle.expansion_ratio**-9
        n_bl = (
            structure.nozzle.material.c_1
            * ((P_0_psi**0.8) / ((structure.nozzle.throat_diameter / 0.0254) ** 0.2))
            * termc_2
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


def get_divergent_correction_factor(divergent_angle: float) -> float:
    """
    Calculates the divergent nozzle correction factor given the half angle.

    Args:
        divergent_angle (float): The half angle of the divergent nozzle.

    Returns:
        float: The divergent correction factor.

    Example:
        correction_factor = get_divergent_correction_factor(15.0)
    """
    return 0.5 * (1 + np.cos(np.deg2rad(divergent_angle)))


def get_expansion_ratio(
    P_e: np.ndarray, P_0: np.ndarray, k: float, critical_pressure_ratio: float
) -> float:
    """
    Calculates the mean expansion ratio based on the pressure ratios.

    Args:
        P_e (np.ndarray): The pressure ratios.
        P_0 (np.ndarray): The chamber stagnation pressures.
        k (float): The isentropic exponent.
        critical_pressure_ratio (float): The critical pressure ratio.

    Returns:
        float: The mean expansion ratio.

    Example:
        expansion_ratio = get_expansion_ratio([5000, 6000], [100000, 150000], 1.4, 0.5)
    """
    E = np.zeros(np.size(P_0))

    for i in range(np.size(P_0)):
        if P_e[i] / P_0[i] <= critical_pressure_ratio:
            pressure_ratio = P_e[i] / P_0[i]
            E[i] = (
                ((k + 1) / 2) ** (1 / (k - 1))
                * pressure_ratio ** (1 / k)
                * ((k + 1) / (k - 1) * (1 - pressure_ratio ** ((k - 1) / k))) ** 0.5
            ) ** -1
        else:
            E[i] = 1
    return np.mean(E)
