from .compressible_flow.isentropic import get_critical_pressure_ratio


def compute_chamber_pressure_mass_balance(
    chamber_pressure: float,
    external_pressure: float,
    mass_flow_in: float,
    free_chamber_volume: float,
    throat_area: float,
    k: float,
    R: float,
    flame_temperature: float,
    nozzle_discharge_coefficient: float = 1.0,
    free_chamber_volume_rate: float = 0.0,
) -> tuple[float]:
    """
    Right-hand side of the chamber pressure ODE from a control-volume mass balance.

    Handles both choked and sub-critical nozzle flow (Seidel 1965, Eq. 35).

    Args:
        chamber_pressure: Chamber pressure [Pa].
        external_pressure: External pressure [Pa].
        mass_flow_in: Mass flow rate into the chamber [kg/s].
        free_chamber_volume: Chamber free volume [m^3].
        throat_area: Nozzle throat area [m^2].
        k: Isentropic exponent of the mix.
        R: Gas constant per molecular weight [J/(kg-K)].
        flame_temperature: Flame temperature [K].
        nozzle_discharge_coefficient: Nozzle discharge coefficient.
        free_chamber_volume_rate: Rate of change of chamber free volume [m^3/s].
            Defaults to 0, i.e. constant free volume.

    Returns:
        Derivative of chamber pressure with respect to time, as a one-tuple.
    """
    critical_pressure_ratio = get_critical_pressure_ratio(k=k)
    pressure_ratio = external_pressure / chamber_pressure

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
        mass_flow_in - mass_flow_out
    ) - chamber_pressure * free_chamber_volume_rate / free_chamber_volume
    return (chamber_pressure_derivative,)
