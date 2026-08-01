import math

import numpy as np

import machwave.core.geometric as geometric

# Below this Reynolds number the flow in a round pipe is taken as laminar.
LAMINAR_REYNOLDS_NUMBER = 2300.0


def get_mass_flow_orifice(
    discharge_coefficient: float,
    area: float,
    density: float,
    pressure_upstream: float,
    pressure_downstream: float,
) -> float:
    """
    Get mass flow rate through an orifice.

    Args:
        discharge_coefficient: Discharge coefficient.
        area: Effective flow area [m^2].
        density: Fluid density [kg/m^3].
        pressure_upstream: Upstream pressure [Pa].
        pressure_downstream: Downstream pressure [Pa].

    Returns:
        Mass flow rate [kg/s].

    Raises:
        ValueError: If downstream pressure exceeds upstream pressure.
    """
    delta_p = pressure_upstream - pressure_downstream
    if delta_p < 0:
        raise ValueError("Pressure downstream cannot be greater than upstream")

    return discharge_coefficient * area * np.sqrt(2.0 * density * delta_p)


def get_reynolds_number(
    density: float,
    velocity: float,
    diameter: float,
    dynamic_viscosity: float,
) -> float:
    """
    Get the Reynolds number of a flow in a round pipe.

    Args:
        density: Fluid density [kg/m^3].
        velocity: Bulk flow velocity [m/s].
        diameter: Internal pipe diameter [m].
        dynamic_viscosity: Fluid dynamic viscosity [Pa-s].

    Returns:
        Reynolds number.

    Raises:
        ValueError: If the dynamic viscosity is not strictly positive.
    """
    if dynamic_viscosity <= 0.0:
        raise ValueError(
            f"dynamic_viscosity must be strictly positive, got {dynamic_viscosity}"
        )

    return density * abs(velocity) * diameter / dynamic_viscosity


def get_darcy_friction_factor(
    reynolds_number: float,
    relative_roughness: float = 0.0,
) -> float:
    """
    Get the Darcy friction factor for a round pipe.

    Laminar flow takes the exact 64 / Re. Turbulent flow takes the Haaland
    correlation, an explicit form of the implicit Colebrook equation that
    stays within a few percent of it over the range of engineering interest.
    The two meet at a step at the laminar limit, where the flow is in
    transition and neither branch describes it well.

    Args:
        reynolds_number: Reynolds number of the flow.
        relative_roughness: Surface roughness over the pipe diameter.

    Returns:
        Darcy friction factor. Zero for a still fluid.
    """
    if reynolds_number <= 0.0:
        return 0.0

    if reynolds_number < LAMINAR_REYNOLDS_NUMBER:
        return 64.0 / reynolds_number

    haaland_term = math.log10(
        (relative_roughness / 3.7) ** 1.11 + 6.9 / reynolds_number
    )
    return 1.0 / (-1.8 * haaland_term) ** 2


def get_pipe_pressure_drop(
    *,
    density: float,
    mass_flow_rate: float,
    length: float,
    diameter: float,
    dynamic_viscosity: float,
    loss_coefficient: float = 0.0,
    relative_roughness: float = 0.0,
) -> float:
    """
    Get the pressure drop along a round pipe by the Darcy-Weisbach equation.

    Fittings, bends and valves enter through `loss_coefficient` by the
    resistance coefficient method, which adds their velocity heads to the ones
    the pipe wall takes.

    Args:
        density: Fluid density [kg/m^3].
        mass_flow_rate: Mass flow rate through the pipe [kg/s].
        length: Pipe length [m].
        diameter: Internal pipe diameter [m].
        dynamic_viscosity: Fluid dynamic viscosity [Pa-s].
        loss_coefficient: Summed resistance coefficient of the fittings.
        relative_roughness: Surface roughness over the pipe diameter.

    Returns:
        Pressure drop [Pa]. Zero for a still fluid.

    Raises:
        ValueError: If the density or the diameter is not strictly positive,
            or if the length or the loss coefficient is negative.
    """
    if density <= 0.0:
        raise ValueError(f"density must be strictly positive, got {density}")
    if diameter <= 0.0:
        raise ValueError(f"diameter must be strictly positive, got {diameter}")
    if length < 0.0:
        raise ValueError(f"length must be non-negative, got {length}")
    if loss_coefficient < 0.0:
        raise ValueError(
            f"loss_coefficient must be non-negative, got {loss_coefficient}"
        )

    if mass_flow_rate <= 0.0:
        return 0.0

    velocity = mass_flow_rate / (density * geometric.get_circle_area(diameter))
    friction_factor = get_darcy_friction_factor(
        get_reynolds_number(density, velocity, diameter, dynamic_viscosity),
        relative_roughness,
    )
    velocity_head_count = friction_factor * length / diameter + loss_coefficient
    return velocity_head_count * density * velocity**2 / 2.0
