from typing import cast

import scipy.optimize


def get_critical_pressure_ratio(k: float) -> float:
    """Get critical pressure ratio for choked flow.

    Args:
        k: Isentropic exponent.

    Returns:
        Critical pressure ratio.
    """
    return (2 / (k + 1)) ** (k / (k - 1))


def get_expansion_ratio_from_exit_mach(mach: float, k: float) -> float:
    """Get expansion ratio from exit Mach number.

    Args:
        mach: Mach number.
        k: Isentropic exponent.

    Returns:
        Expansion ratio (A / A_throat).
    """
    term1 = (2 / (k + 1)) * (1 + 0.5 * (k - 1) * mach**2)
    term2 = (k + 1) / (2 * (k - 1))
    return (1 / mach) * (term1**term2)


def get_exit_mach_from_expansion_ratio(k: float, expansion_ratio: float) -> float:
    """Get exit Mach number from expansion ratio.

    Args:
        k: Isentropic exponent.
        expansion_ratio: Expansion ratio (A_exit / A_throat).

    Returns:
        Exit Mach number.

    Raises:
        ValueError: If solver fails to converge.
    """
    try:
        exit_mach = cast(
            float,
            scipy.optimize.brentq(
                lambda m: get_expansion_ratio_from_exit_mach(m, k) - expansion_ratio,
                a=1.001,  # Just above sonic
                b=20.0,  # High supersonic
            ),
        )
        return exit_mach
    except ValueError as e:
        raise ValueError(
            f"Failed to converge for expansion_ratio={expansion_ratio}, k={k}"
        ) from e


def get_exit_pressure(
    k_exhaust: float,
    expansion_ratio: float,
    chamber_pressure: float,
) -> float:
    """Get exit pressure from isentropic relations.

    Args:
        k_exhaust: Isentropic exponent at exit.
        expansion_ratio: Expansion ratio.
        chamber_pressure: Chamber pressure [Pa].

    Returns:
        Exit pressure [Pa].
    """
    exit_mach = get_exit_mach_from_expansion_ratio(k_exhaust, expansion_ratio)
    return chamber_pressure * (1 + 0.5 * (k_exhaust - 1) * exit_mach**2) ** (
        -k_exhaust / (k_exhaust - 1)
    )


def is_flow_choked(
    chamber_pressure: float,
    external_pressure: float,
    critical_pressure_ratio: float,
) -> bool:
    """Check if flow is choked.

    Args:
        chamber_pressure: Chamber pressure [Pa].
        external_pressure: External pressure [Pa].
        critical_pressure_ratio: Critical pressure ratio.

    Returns:
        True if flow is choked, False otherwise.
    """
    return chamber_pressure >= external_pressure / critical_pressure_ratio
