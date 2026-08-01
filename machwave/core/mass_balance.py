from typing import Callable

from .compressible_flow.isentropic import get_critical_pressure_ratio


def _zero_volume_rate(chamber_pressure: float) -> float:
    """Free chamber volume rate for a rigid chamber: zero at any pressure."""
    return 0.0


def compute_chamber_pressure_mass_balance(
    chamber_pressure: float,
    external_pressure: float,
    mass_flow_in: Callable[[float], float],
    free_chamber_volume: float,
    throat_area: float,
    k: float,
    R: float,
    flame_temperature: float,
    nozzle_discharge_coefficient: float = 1.0,
    free_chamber_volume_rate: Callable[[float], float] = _zero_volume_rate,
) -> tuple[float]:
    """
    Right-hand side of the chamber pressure ODE from a control-volume mass balance.

    Handles both choked and sub-critical nozzle flow (Seidel 1965, Eq. 35).

    Args:
        chamber_pressure: Chamber pressure [Pa].
        external_pressure: External pressure [Pa].
        mass_flow_in: Callable mapping chamber pressure to the mass flow rate
            into the chamber [kg/s]. It is evaluated at each Runge-Kutta stage
            pressure, keeping the pressure-dependent inflow consistent with
            the outflow term.
        free_chamber_volume: Chamber free volume [m^3].
        throat_area: Nozzle throat area [m^2].
        k: Isentropic exponent of the mix.
        R: Gas constant per molecular weight [J/(kg-K)].
        flame_temperature: Effective flame temperature [K].
        nozzle_discharge_coefficient: Nozzle discharge coefficient.
        free_chamber_volume_rate: Callable mapping chamber pressure to the rate
            of change of chamber free volume [m^3/s]. Defaults to a callable
            returning 0, i.e. constant free volume.

    Returns:
        Derivative of chamber pressure with respect to time, as a one-tuple.
    """
    inflow = mass_flow_in(chamber_pressure)
    volume_rate = free_chamber_volume_rate(chamber_pressure)

    critical_pressure_ratio = get_critical_pressure_ratio(k=k)
    # A chamber at or below ambient drives nothing out of the nozzle. Holding
    # the ratio at one takes the sub-critical branch to zero outflow there,
    # rather than to the root of a negative number; flow back in through the
    # nozzle is not modeled.
    pressure_ratio = min(external_pressure / chamber_pressure, 1.0)

    if pressure_ratio <= critical_pressure_ratio:  # choked
        isentropic_flow_function = (k**0.5) * (2 / (k + 1)) ** (
            (k + 1) / (2 * (k - 1))
        )  # Vandenkerckhove function
    else:
        isentropic_flow_function = (
            ((2 * k / (k - 1)) ** 0.5)
            * pressure_ratio ** (1 / k)
            * (1 - pressure_ratio ** ((k - 1) / k)) ** 0.5
        )

    mass_flow_out = (
        nozzle_discharge_coefficient
        * chamber_pressure
        * throat_area
        * isentropic_flow_function
        / (R * flame_temperature) ** 0.5
    )

    chamber_pressure_derivative = (R * flame_temperature / free_chamber_volume) * (
        inflow - mass_flow_out
    ) - chamber_pressure * volume_rate / free_chamber_volume
    return (chamber_pressure_derivative,)
