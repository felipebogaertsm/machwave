"""
Solid rocket motor chamber pressure mass balance differential equation.
"""

from ..compressible_flow.isentropic import get_critical_pressure_ratio


def compute_chamber_pressure_mass_balance_srm(
    P0: float,
    Pe: float,
    Ab: float,
    V0: float,
    At: float,
    pp: float,
    k: float,
    R: float,
    T0: float,
    r: float,
    Cd: float = 1.0,
) -> tuple[float]:
    """
    Calculates the chamber pressure by solving Hans Seidel's differential equation.

    This differential equation was presented in Seidel's paper named "Transient Chamber
    Pressure and Thrust in Solid Rocket Motors", published in March, 1965.

    Args:
        P0: Chamber pressure [Pa].
        Pe: External pressure [Pa].
        Ab: Burn area [m^2].
        V0: Chamber free volume [m^3].
        At: Nozzle throat area [m^2].
        pp: Propellant density [kg/m^3].
        k: Isentropic exponent of the mix.
        R: Gas constant per molecular weight [J/(kg·K)].
        T0: Flame temperature [K].
        r: Propellant burn rate [m/s].
        Cd: Discharge coefficient, default is 1.0.

    Returns:
        Derivative of chamber pressure with respect to time.

    """
    critical_pressure_ratio = get_critical_pressure_ratio(k=k)
    Pr = Pe / P0

    if Pr <= critical_pressure_ratio:  # choked
        H = (k**0.5) * (2 / (k + 1)) ** ((k + 1) / (2 * (k - 1)))
    else:  # sub-critical (Seidel 1965, Eq. 35)
        H = (
            ((2 * k / (k - 1)) ** 0.5)
            * Pr ** (1 / k)
            * (1 - Pr ** ((k - 1) / k)) ** 0.5
        )

    m_dot_gen = pp * r * Ab
    m_dot_exit = Cd * P0 * At * H / (R * T0) ** 0.5

    dP0_dt = (R * T0 / V0) * (m_dot_gen - m_dot_exit)
    return (dP0_dt,)
