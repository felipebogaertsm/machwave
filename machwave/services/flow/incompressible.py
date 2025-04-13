import numpy as np


def mass_flow_orifice(
    C_d: float, A: float, rho: float, p_up: float, p_down: float
) -> float:
    """
    Calculates the mass flow rate through an orifice under the assumption of incompressible flow.

    Args:
        C_d: Discharge coefficient.
        A: Effective flow area of the orifice.
        rho: Density of the fluid.
        p_up: Upstream pressure.
        p_down: Downstream pressure.

    Returns:
      The mass flow rate through the orifice. Returns 0 if the pressure difference is zero or negative.
    """
    delta_p = p_up - p_down
    if delta_p <= 0:
        raise ValueError("Pressure upstream must be greater than downstream.")

    return C_d * A * np.sqrt(2.0 * rho * delta_p)
