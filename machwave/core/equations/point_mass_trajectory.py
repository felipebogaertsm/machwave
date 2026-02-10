"""
Point mass trajectory equation.
"""


def compute_point_mass_trajectory(
    y: float, v: float, T: float, D: float, M: float, g: float
) -> tuple[float, float]:
    """
    Returns the derivatives of elevation and velocity.

    Args:
        y: Instant elevation [m].
        v: Instant velocity [m/s].
        T: Instant thrust [N].
        D: Instant drag constant (Cd * A * rho / 2) [kg/m].
        M: Instant total mass [kg].
        g: Instant acceleration of gravity [m/s^2].

    Returns:
        Derivatives of elevation and velocity.
    """
    if v < 0:
        x = -1
    else:
        x = 1

    dv_dt = (T - x * D * (v**2)) / M - g
    dy_dt = v

    return (dy_dt, dv_dt)
