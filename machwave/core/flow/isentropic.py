import numpy as np
import scipy.optimize


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


def get_opt_expansion_ratio(
    k: float, chamber_pressure: float, atmospheric_pressurext: float
) -> float:
    """
    Returns the optimal expansion ratio based on the current chamber pressure,
    specific heat ratio, and external pressure.

    Args:
        k (float): The isentropic exponent.
        chamber_pressure (float): The chamber pressure.
        atmospheric_pressurext (float): The external pressure.

    Returns:
        float: The optimal expansion ratio.

    Example:
        expansion_ratio = get_opt_expansion_ratio(1.4, 100000, 10000)
    """
    exp_opt = (
        (((k + 1) / 2) ** (1 / (k - 1)))
        * ((atmospheric_pressurext / chamber_pressure) ** (1 / k))
        * np.sqrt(
            ((k + 1) / (k - 1))
            * (1 - (atmospheric_pressurext / chamber_pressure) ** ((k - 1) / k))
        )
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


def get_exit_pressure(
    k_ex: float, expansion_ratio: float, chamber_pressure: float
) -> float:
    """
    Calculates the exit pressure of the nozzle flow.

    Args:
        k_ex (float): The isentropic exponent in the exit region.
        expansion_ratio (float): The expansion ratio.
        chamber_pressure (float): The chamber pressure.

    Returns:
        float: The exit pressure.

    Example:
        exit_pressure = get_exit_pressure(1.4, 5.0, 100000)
    """
    exit_mach = get_exit_mach(k_ex, expansion_ratio)
    exit_pressure = chamber_pressure * (1 + 0.5 * (k_ex - 1) * exit_mach**2) ** (
        -k_ex / (k_ex - 1)
    )
    return exit_pressure


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
    chamber_pressure: float,
    exit_pressure: float,
    atmospheric_pressure: float,
    expansion_ratio: float,
    k: float,
    nozzle_correction_factor: float,
) -> tuple[float, float]:
    """
    Calculates the thrust coefficients based on the chamber pressure and correction factor.

    Args:
        chamber_pressure (float): The chamber pressure.
        exit_pressure (float): The exit pressure.
        atmospheric_pressure (float): The external pressure.
        expansion_ratio (float): The expansion ratio.
        k (float): The isentropic exponent.
        nozzle_correction_factor (float): The correction factor.

    Returns:
        tuple[float, float]: The thrust coefficients (Cf, Cf_ideal).

    Example:
        Cf, Cf_ideal = get_thrust_coefficients(100000, 5000, 1000, 5.0, 1.4, 0.8)
    """
    Cf_ideal = get_ideal_thrust_coefficient(
        chamber_pressure, exit_pressure, atmospheric_pressure, expansion_ratio, k
    )
    Cf = Cf_ideal * nozzle_correction_factor

    if Cf <= 0:
        Cf = 0
    if Cf_ideal <= 0:
        Cf_ideal = 0

    return Cf, Cf_ideal


def get_thrust_from_cf(
    thrust_coefficient: float, chamber_pressure: float, nozzle_throat_area: float
) -> float:
    """
    Calculates the thrust based on the thrust coefficient, chamber stagnation pressure,
    and nozzle throat area.

    Args:
        thrust_coefficient (float): The thrust coefficient.
        chamber_pressure (float): The chamber stagnation pressure.
        nozzle_throat_area (float): The nozzle throat area.

    Returns:
        float: The thrust.

    Example:
        thrust = get_thrust_from_cf(0.8, 100000, 0.02)
    """
    return thrust_coefficient * chamber_pressure * nozzle_throat_area


def get_thrust_coefficient(
    chamber_pressure: float, thrust: float, nozzle_throat_area: float
) -> float:
    """
    Calculates the thrust coefficient based on the chamber stagnation pressure, thrust,
    and nozzle throat area.

    Args:
        chamber_pressure (float): The chamber stagnation pressure.
        thrust (float): The thrust.
        nozzle_throat_area (float): The nozzle throat area.

    Returns:
        float: The thrust coefficient.

    Example:
        Cf = get_thrust_coefficient(100000, 5000, 0.02)
    """
    return thrust / (chamber_pressure * nozzle_throat_area)


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
    Calculates the total impulse of the state based on the average thrust and thrust time.

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
    Calculates the specific impulse of the state based on the total impulse and initial propellant mass.

    Args:
        total_impulse (float): The total impulse.
        initial_propellant_mass (float): The initial propellant mass.

    Returns:
        float: The specific impulse.

    Example:
        specific_impulse = get_specific_impulse(15000, 100)
    """
    return total_impulse / initial_propellant_mass / 9.81


def get_expansion_ratio(
    atmospheric_pressure: np.ndarray,
    chamber_pressure: np.ndarray,
    k: float,
    critical_pressure_ratio: float,
) -> float:
    """
    Calculates the mean expansion ratio based on the pressure ratios.

    Args:
        atmospheric_pressure (np.ndarray): The pressure ratios.
        chamber_pressure (np.ndarray): The chamber stagnation pressures.
        k (float): The isentropic exponent.
        critical_pressure_ratio (float): The critical pressure ratio.

    Returns:
        float: The mean expansion ratio.

    Example:
        expansion_ratio = get_expansion_ratio([5000, 6000], [100000, 150000], 1.4, 0.5)
    """
    expansion_ratio = np.zeros(np.size(chamber_pressure))

    for i in range(np.size(chamber_pressure)):
        if atmospheric_pressure[i] / chamber_pressure[i] <= critical_pressure_ratio:
            pressure_ratio = atmospheric_pressure[i] / chamber_pressure[i]
            expansion_ratio[i] = (
                ((k + 1) / 2) ** (1 / (k - 1))
                * pressure_ratio ** (1 / k)
                * ((k + 1) / (k - 1) * (1 - pressure_ratio ** ((k - 1) / k))) ** 0.5
            ) ** -1
        else:
            expansion_ratio[i] = 1
    return np.mean(expansion_ratio)
