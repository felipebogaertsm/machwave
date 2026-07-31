import enum
from typing import cast

import scipy.optimize

SONIC_MACH = 1.0


class FlowBranch(enum.StrEnum):
    """Branch of the area-Mach relation that a solution is taken from."""

    SUBSONIC = "subsonic"
    SUPERSONIC = "supersonic"


MACH_LIMITS: dict[FlowBranch, float] = {
    FlowBranch.SUBSONIC: 1e-6,
    FlowBranch.SUPERSONIC: 20.0,
}


def get_critical_pressure_ratio(k: float) -> float:
    """
    Get critical pressure ratio for choked flow.

    Args:
        k: Isentropic exponent.

    Returns:
        Critical pressure ratio.
    """
    return (2 / (k + 1)) ** (k / (k - 1))


def get_expansion_ratio_from_exit_mach(mach: float, k: float) -> float:
    """
    Get expansion ratio from exit Mach number.

    Args:
        mach: Mach number.
        k: Isentropic exponent.

    Returns:
        Expansion ratio (A / A_throat).
    """
    term1 = (2 / (k + 1)) * (1 + 0.5 * (k - 1) * mach**2)
    term2 = (k + 1) / (2 * (k - 1))
    return (1 / mach) * (term1**term2)


def get_maximum_expansion_ratio(k: float, branch: FlowBranch) -> float:
    """
    Get the largest expansion ratio the exit Mach solver resolves on a branch.

    Args:
        k: Isentropic exponent.
        branch: Branch of the area-Mach relation.

    Returns:
        Expansion ratio at the Mach limit of the branch.
    """
    return get_expansion_ratio_from_exit_mach(MACH_LIMITS[branch], k)


def get_exit_mach_from_expansion_ratio(
    k: float,
    expansion_ratio: float,
    branch: FlowBranch = FlowBranch.SUPERSONIC,
) -> float:
    """
    Get exit Mach number from expansion ratio.

    Every expansion ratio above unity satisfies the area-Mach relation at one
    subsonic and one supersonic Mach number. The supersonic root is returned by
    default, which is the started nozzle flowing full. A nozzle that is not started
    carries a normal shock in its divergent section and leaves subsonically, so its
    physical root is the subsonic one and has to be asked for explicitly.

    Args:
        k: Isentropic exponent.
        expansion_ratio: Expansion ratio (A_exit / A_throat).
        branch: Branch of the area-Mach relation to solve on.

    Returns:
        Exit Mach number.

    Raises:
        ValueError: If the expansion ratio lies outside the range the branch covers.
    """
    mach_limit = MACH_LIMITS[branch]
    maximum_expansion_ratio = get_maximum_expansion_ratio(k, branch)
    if not 1.0 <= expansion_ratio <= maximum_expansion_ratio:
        raise ValueError(
            f"Expansion ratio {expansion_ratio} has no {branch} solution for "
            f"isentropic exponent {k}. The {branch} branch covers expansion ratios "
            f"from 1 at the sonic throat to {maximum_expansion_ratio:.6g} at the "
            f"Mach {mach_limit:g} limit of the solver."
        )

    if expansion_ratio <= get_expansion_ratio_from_exit_mach(SONIC_MACH, k):
        return SONIC_MACH  # Both roots meet at the throat.

    return cast(
        float,
        scipy.optimize.brentq(
            lambda m: get_expansion_ratio_from_exit_mach(m, k) - expansion_ratio,
            a=min(SONIC_MACH, mach_limit),
            b=max(SONIC_MACH, mach_limit),
        ),
    )


def get_exit_pressure(
    k_exhaust: float,
    expansion_ratio: float,
    chamber_pressure: float,
    branch: FlowBranch = FlowBranch.SUPERSONIC,
) -> float:
    """
    Get exit pressure from isentropic relations.

    Args:
        k_exhaust: Isentropic exponent at exit.
        expansion_ratio: Expansion ratio.
        chamber_pressure: Chamber pressure [Pa].
        branch: Branch of the area-Mach relation to solve the exit Mach number on.

    Returns:
        Exit pressure [Pa].
    """
    exit_mach = get_exit_mach_from_expansion_ratio(k_exhaust, expansion_ratio, branch)
    return chamber_pressure * (1 + 0.5 * (k_exhaust - 1) * exit_mach**2) ** (
        -k_exhaust / (k_exhaust - 1)
    )


def is_flow_choked(
    chamber_pressure: float,
    external_pressure: float,
    critical_pressure_ratio: float,
) -> bool:
    """
    Check if flow is choked.

    Args:
        chamber_pressure: Chamber pressure [Pa].
        external_pressure: External pressure [Pa].
        critical_pressure_ratio: Critical pressure ratio.

    Returns:
        True if flow is choked, False otherwise.
    """
    return chamber_pressure >= external_pressure / critical_pressure_ratio
