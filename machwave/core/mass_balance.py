from .compressible_flow.isentropic import get_critical_pressure_ratio


def compute_chamber_pressure_mass_balance(
    P0: float,
    Pe: float,
    m_in: float,
    V0: float,
    At: float,
    k: float,
    R: float,
    T0: float,
    Cd: float = 1.0,
) -> tuple[float]:
    """
    Right-hand side of the chamber pressure ODE from a control-volume mass balance.

    Handles both choked and sub-critical nozzle flow (Seidel 1965, Eq. 35).

    Args:
        P0: Chamber pressure [Pa].
        Pe: External pressure [Pa].
        m_in: Mass flow rate into the chamber [kg/s].
        V0: Chamber free volume [m^3].
        At: Nozzle throat area [m^2].
        k: Isentropic exponent of the mix.
        R: Gas constant per molecular weight [J/(kg·K)].
        T0: Flame temperature [K].
        Cd: Discharge coefficient.

    Returns:
        Derivative of chamber pressure with respect to time, as a one-tuple.
    """
    critical_pressure_ratio = get_critical_pressure_ratio(k=k)
    Pr = Pe / P0

    if Pr <= critical_pressure_ratio:  # choked
        H = (k**0.5) * (2 / (k + 1)) ** ((k + 1) / (2 * (k - 1)))
    else:
        H = (
            ((2 * k / (k - 1)) ** 0.5)
            * Pr ** (1 / k)
            * (1 - Pr ** ((k - 1) / k)) ** 0.5
        )

    m_out = Cd * P0 * At * H / (R * T0) ** 0.5

    dP0_dt = (R * T0 / V0) * (m_in - m_out)
    return (dP0_dt,)
