import numpy as np


def get_optimal_expansion_ratio(
    k: float, chamber_pressure: float, atmospheric_pressure: float
) -> float:
    """Get optimal expansion ratio for DeLaval nozzle.

    Args:
        k: Isentropic exponent.
        chamber_pressure: Chamber pressure [Pa].
        atmospheric_pressure: External pressure [Pa].

    Returns:
        Optimal expansion ratio.
    """
    return (
        (((k + 1) / 2) ** (1 / (k - 1)))
        * ((atmospheric_pressure / chamber_pressure) ** (1 / k))
        * np.sqrt(
            ((k + 1) / (k - 1))
            * (1 - (atmospheric_pressure / chamber_pressure) ** ((k - 1) / k))
        )
    ) ** -1


def get_ideal_thrust_coefficient(
    chamber_pressure: float,
    exit_pressure: float,
    external_pressure: float,
    expansion_ratio: float,
    k_ex: float,
) -> float:
    """Get ideal thrust coefficient for DeLaval nozzle.

    Args:
        chamber_pressure: Chamber pressure [Pa].
        exit_pressure: Exit pressure [Pa].
        external_pressure: External pressure [Pa].
        expansion_ratio: Expansion ratio.
        k_ex: Isentropic exponent at exit.

    Returns:
        Ideal thrust coefficient.

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
    """Apply nozzle efficiency correction to thrust coefficient.

    Args:
        ideal_thrust_coefficient: Ideal thrust coefficient.
        nozzle_correction_factor: Nozzle efficiency (0-1).

    Returns:
        Corrected thrust coefficient.
    """
    return ideal_thrust_coefficient * nozzle_correction_factor
