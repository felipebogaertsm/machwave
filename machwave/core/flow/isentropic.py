import numpy as np
import scipy.optimize
import scipy.constants


def get_critical_pressure_ratio(k: float) -> float:
    """
    Calculates the critical pressure ratio for choked flow.

    Args:
        k: The isentropic exponent.

    Returns:
        The critical pressure ratio.
    """
    return (2 / (k + 1)) ** (k / (k - 1))


def get_optimal_expansion_ratio(
    k: float, chamber_pressure: float, atmospheric_pressure: float
) -> float:
    """
    Calculates the optimal expansion ratio for a DeLaval nozzle.

    Args:
        k: The isentropic exponent.
        chamber_pressure: The chamber pressure [Pa].
        atmospheric_pressure: The external pressure [Pa].

    Returns:
        The optimal expansion ratio.
    """
    return (
        (((k + 1) / 2) ** (1 / (k - 1)))
        * ((atmospheric_pressure / chamber_pressure) ** (1 / k))
        * np.sqrt(
            ((k + 1) / (k - 1))
            * (1 - (atmospheric_pressure / chamber_pressure) ** ((k - 1) / k))
        )
    ) ** -1


def get_exit_mach(k: float, expansion_ratio: float, initial_guess: float = 10) -> float:
    """
    Calculates the exit Mach number for a DeLaval nozzle.

    Uses a numerical solver to find the root.

    Args:
        k: The isentropic exponent.
        expansion_ratio: The expansion ratio.
        initial_guess: Initial guess for the exit Mach number.

    Returns:
        The exit Mach number.
    """
    exit_mach_no = scipy.optimize.fsolve(
        lambda x: (
            ((1 + 0.5 * (k - 1) * x**2) / (1 + 0.5 * (k - 1)))
            ** ((k + 1) / (2 * (k - 1)))
        )
        / x
        - expansion_ratio,
        [initial_guess],
    )
    return exit_mach_no[0]


def get_exit_pressure(
    k_ex: float, expansion_ratio: float, chamber_pressure: float
) -> float:
    """
    Calculates the exit pressure of a DeLaval nozzle.

    Args:
        k_ex: The isentropic exponent in the exit region.
        expansion_ratio: The expansion ratio.
        chamber_pressure: The chamber pressure [Pa].

    Returns:
        The exit pressure [Pa].
    """
    exit_mach = get_exit_mach(k_ex, expansion_ratio)
    return chamber_pressure * (1 + 0.5 * (k_ex - 1) * exit_mach**2) ** (
        -k_ex / (k_ex - 1)
    )


def get_ideal_thrust_coefficient(
    chamber_pressure: float,
    exit_pressure: float,
    external_pressure: float,
    expansion_ratio: float,
    k_ex: float,
) -> float:
    """
    Calculates the thrust coefficient.

    Args:
        chamber_pressure: The chamber pressure [Pa].
        exit_pressure: The exit pressure [Pa].
        external_pressure: The external pressure [Pa].
        expansion_ratio: The expansion ratio.
        k_ex: The isentropic exponent in the exit region.

    Returns:
        The thrust coefficient.

    References:
        https://www.nakka-rocketry.net/th_thrst.html
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


def apply_thrust_coefficient_correction(
    ideal_thrust_coefficient: float,
    nozzle_correction_factor: float,
) -> float:
    """
    Applies the nozzle correction factor to the ideal thrust coefficient.

    Args:
        ideal_thrust_coefficient: The ideal thrust coefficient.
        nozzle_correction_factor: The nozzle correction factor representing losses
            (0-1).

    Returns:
        The real thrust coefficient.
    """
    return ideal_thrust_coefficient * nozzle_correction_factor


def get_thrust_from_thrust_coefficient(
    thrust_coefficient: float, chamber_pressure: float, nozzle_throat_area: float
) -> float:
    """
    Calculates the thrust based on the thrust coefficient, chamber stagnation pressure,
    and nozzle throat area.

    Args:
        thrust_coefficient: The thrust coefficient.
        chamber_pressure: The chamber stagnation pressure [Pa].
        nozzle_throat_area: The nozzle throat area [m^2].

    Returns:
        The thrust [N].
    """
    return thrust_coefficient * chamber_pressure * nozzle_throat_area


def get_thrust_coefficient_from_thrust(
    chamber_pressure: float, thrust: float, nozzle_throat_area: float
) -> float:
    """
    Calculates the thrust coefficient based on the chamber stagnation pressure, thrust,
    and nozzle throat area.

    Args:
        chamber_pressure: The chamber stagnation pressure [Pa].
        thrust: The thrust [N].
        nozzle_throat_area: The nozzle throat area [m^2].

    Returns:
        The thrust coefficient.
    """
    return thrust / (chamber_pressure * nozzle_throat_area)


def is_flow_choked(
    chamber_pressure: float,
    external_pressure: float,
    critical_pressure_ratio: float,
) -> bool:
    """
    Determines if the flow is choked based on the chamber pressure, external pressure,
    and critical pressure ratio.

    Args:
        chamber_pressure: The chamber pressure [Pa].
        external_pressure: The external pressure [Pa].
        critical_pressure_ratio: The critical pressure ratio.

    Returns:
        True if the flow is choked, False otherwise.
    """
    return chamber_pressure >= external_pressure / critical_pressure_ratio


def get_total_impulse(average_thrust: float, thrust_time: float) -> float:
    """
    Calculates the total impulse based on the average thrust and thrust time.

    Args:
        average_thrust: The average thrust [N].
        thrust_time: The thrust time [s].

    Returns:
        The total impulse [N-s].
    """
    return average_thrust * thrust_time


def get_specific_impulse(total_impulse: float, initial_propellant_mass: float) -> float:
    """
    Calculates the specific impulse based on the total impulse and initial propellant
    mass.

    Args:
        total_impulse: The total impulse [N-s].
        initial_propellant_mass: The initial propellant mass [kg].

    Returns:
        The specific impulse [s].
    """
    return total_impulse / initial_propellant_mass / scipy.constants.g


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
