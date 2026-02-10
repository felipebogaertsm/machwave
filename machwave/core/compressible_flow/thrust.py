"""
Thrust coefficient calculations for compressible nozzle flow.
"""


def get_thrust_from_thrust_coefficient(
    thrust_coefficient: float, chamber_pressure: float, nozzle_throat_area: float
) -> float:
    """Get thrust from thrust coefficient.

    Args:
        thrust_coefficient: Thrust coefficient.
        chamber_pressure: Chamber stagnation pressure [Pa].
        nozzle_throat_area: Nozzle throat area [m^2].

    Returns:
        Thrust [N].
    """
    return thrust_coefficient * chamber_pressure * nozzle_throat_area


def get_thrust_coefficient_from_thrust(
    chamber_pressure: float, thrust: float, nozzle_throat_area: float
) -> float:
    """Get thrust coefficient from thrust.

    Args:
        chamber_pressure: Chamber stagnation pressure [Pa].
        thrust: Thrust [N].
        nozzle_throat_area: Nozzle throat area [m^2].

    Returns:
        Thrust coefficient.
    """
    return thrust / (chamber_pressure * nozzle_throat_area)


__all__ = ["get_thrust_from_thrust_coefficient", "get_thrust_coefficient_from_thrust"]
