from typing import cast

import numpy as np
import scipy.optimize

import machwave.core.compressible_flow.isentropic as isentropic


def get_optimal_expansion_ratio(
    k: float, chamber_pressure: float, atmospheric_pressure: float
) -> float:
    """
    Get optimal expansion ratio for DeLaval nozzle.

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


def get_separated_exit_conditions(
    k_exhaust: float,
    expansion_ratio: float,
    chamber_pressure: float,
    external_pressure: float,
    separation_pressure_ratio: float,
) -> tuple[float, float]:
    """
    Get the effective exit conditions accounting for flow separation.

    The model implemented is based on the work of Summerfield et al. (1954) and assumes
    that flow separation occurs when the exit pressure is below a certain fraction of
    the ambient pressure.

    Args:
        k_exhaust: Isentropic exponent at exit.
        expansion_ratio: Geometric expansion ratio.
        chamber_pressure: Chamber pressure [Pa].
        external_pressure: Ambient pressure [Pa].
        separation_pressure_ratio: Separation-to-ambient pressure ratio.

    Returns:
        Effective expansion ratio and effective exit pressure [Pa]. The effective
        expansion ratio never falls below the throat value of unity.

    Raises:
        ValueError: If the geometric expansion ratio lies outside the range the
            supersonic branch of the area-Mach relation covers.

    References:
        Summerfield, M., Foster, C. R., & Swan, W. C. (1954). Flow separation in
        overexpanded supersonic exhaust nozzles.
    """
    exit_pressure = isentropic.get_exit_pressure(
        k_exhaust, expansion_ratio, chamber_pressure
    )
    separation_pressure = separation_pressure_ratio * external_pressure
    if exit_pressure >= separation_pressure:
        return expansion_ratio, exit_pressure

    sonic_pressure = chamber_pressure * isentropic.get_critical_pressure_ratio(
        k_exhaust
    )
    if separation_pressure >= sonic_pressure:
        return 1.0, sonic_pressure

    # The exit pressure falls monotonically from the sonic throat to the geometric
    # exit, so bracketing from the throat always contains the separation point.
    effective_expansion_ratio = cast(
        float,
        scipy.optimize.brentq(
            lambda ratio: (
                isentropic.get_exit_pressure(k_exhaust, ratio, chamber_pressure)
                - separation_pressure
            ),
            a=1.0,
            b=expansion_ratio,
        ),
    )
    return effective_expansion_ratio, separation_pressure


def get_ideal_thrust_coefficient_terms(
    chamber_pressure: float,
    exit_pressure: float,
    external_pressure: float,
    expansion_ratio: float,
    k_exhaust: float,
) -> tuple[float, float]:
    """
    Get the momentum and pressure terms of the ideal thrust coefficient.

    Args:
        chamber_pressure: Chamber pressure [Pa].
        exit_pressure: Exit pressure [Pa].
        external_pressure: External pressure [Pa].
        expansion_ratio: Expansion ratio.
        k_exhaust: Isentropic exponent at exit.

    Returns:
        Momentum term then pressure term. The pressure term is positive when under
        expanded and negative when over expanded.

    References:
        https://www.nakka-rocketry.net/th_thrst.html
    """
    pressure_ratio = exit_pressure / chamber_pressure
    momentum_term = np.sqrt(
        (2 * (k_exhaust**2) / (k_exhaust - 1))
        * ((2 / (k_exhaust + 1)) ** ((k_exhaust + 1) / (k_exhaust - 1)))
        * (1 - (pressure_ratio ** ((k_exhaust - 1) / k_exhaust)))
    )
    pressure_term = (
        expansion_ratio * (exit_pressure - external_pressure) / chamber_pressure
    )
    return momentum_term, pressure_term


def get_thrust_from_thrust_coefficient(
    thrust_coefficient: float, chamber_pressure: float, nozzle_throat_area: float
) -> float:
    """
    Get thrust from thrust coefficient.

    Args:
        thrust_coefficient: Thrust coefficient.
        chamber_pressure: Chamber stagnation pressure [Pa].
        nozzle_throat_area: Nozzle throat area [m^2].

    Returns:
        Thrust [N].
    """
    return thrust_coefficient * chamber_pressure * nozzle_throat_area
