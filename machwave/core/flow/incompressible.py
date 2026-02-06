import numpy as np


def get_mass_flow_orifice(
    discharge_coefficient: float,
    area: float,
    density: float,
    pressure_upstream: float,
    pressure_downstream: float,
) -> float:
    """
    Calculates the mass flow rate through an orifice under the assumption of
    incompressible flow.

    Args:
        discharge_coefficient: Discharge coefficient.
        area: Effective flow area of the orifice [m^2].
        density: Density of the fluid [kg/m^3].
        pressure_upstream: Upstream pressure [Pa].
        pressure_downstream: Downstream pressure [Pa].

    Returns:
        The mass flow rate through the orifice [kg/s].

    Raises:
        ValueError: If the downstream pressure is greater than the upstream pressure.
    """
    delta_p = pressure_upstream - pressure_downstream
    if delta_p < 0:
        raise ValueError("Pressure downstream cannot be greater than upstream")

    return discharge_coefficient * area * np.sqrt(2.0 * density * delta_p)
