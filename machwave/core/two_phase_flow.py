import CoolProp.CoolProp as CP
import numpy as np


def get_homogeneous_equilibrium_mass_flux(
    fluid_name: str,
    temperature_upstream: float,
    pressure_downstream: float,
    pressure_upstream: float | None = None,
    sweep_points: int = 200,
) -> float:
    """
    Get the mass flux through an orifice via the homogeneous-equilibrium model.

    Sweeps the pressure from downstream to upstream to find the maximum mass flux.
    Returns the choked mass flux when the orifice is critical, otherwise the value at
    the downstream pressure.

    Args:
        fluid_name: CoolProp fluid name.
        temperature_upstream: Upstream stagnation temperature [K].
        pressure_downstream: Downstream pressure [Pa].
        pressure_upstream: Upstream stagnation pressure [Pa]. If `None`, the saturation
            pressure at the upstream temperature is used.
        sweep_points: Number of pressure points in the isentropic sweep.

    Returns:
        Mass flux [kg/(m^2-s)]. Zero if the downstream pressure is at or above the
        upstream pressure.

    Raises:
        ValueError: If the number of sweep points is less than 2.
    """
    if sweep_points < 2:
        raise ValueError("sweep_points must be at least 2")

    upstream_pressure = (
        CP.PropsSI("P", "T", temperature_upstream, "Q", 0, fluid_name)
        if pressure_upstream is None
        else pressure_upstream
    )

    if pressure_downstream >= upstream_pressure:
        return 0.0

    upstream_enthalpy, upstream_entropy = _get_stagnation_enthalpy_and_entropy(
        fluid_name, temperature_upstream, upstream_pressure
    )

    pressures = np.linspace(pressure_downstream, upstream_pressure, sweep_points)
    mass_flux = np.zeros_like(pressures)
    for index, pressure in enumerate(pressures):
        mass_flux[index] = _get_isentropic_mass_flux(
            fluid_name, pressure, upstream_enthalpy, upstream_entropy
        )

    return float(mass_flux.max())


def _get_stagnation_enthalpy_and_entropy(
    fluid_name: str,
    temperature: float,
    pressure: float,
) -> tuple[float, float]:
    """
    Get enthalpy and entropy at a given pressure and temperature.

    Falls back to the saturated-liquid state at the requested temperature
    when the pressure-temperature pair lies on the saturation curve.

    Args:
        fluid_name: CoolProp fluid name.
        temperature: Stagnation temperature [K].
        pressure: Stagnation pressure [Pa].

    Returns:
        Tuple of enthalpy [J/kg] and entropy [J/(kg K)].
    """
    try:
        enthalpy = CP.PropsSI("H", "P", pressure, "T", temperature, fluid_name)
        entropy = CP.PropsSI("S", "P", pressure, "T", temperature, fluid_name)
        return enthalpy, entropy
    except ValueError:
        enthalpy = CP.PropsSI("H", "T", temperature, "Q", 0, fluid_name)
        entropy = CP.PropsSI("S", "T", temperature, "Q", 0, fluid_name)
        return enthalpy, entropy


def _get_isentropic_mass_flux(
    fluid_name: str,
    pressure: float,
    enthalpy_upstream: float,
    entropy_upstream: float,
) -> float:
    """
    Get the isentropic mass flux at a given pressure for a known upstream state.

    Args:
        fluid_name: CoolProp fluid name.
        pressure: Downstream pressure [Pa].
        enthalpy_upstream: Upstream stagnation enthalpy [J/kg].
        entropy_upstream: Upstream stagnation entropy [J/(kg K)].

    Returns:
        Mass flux [kg/(m^2-s)]. Zero if the downstream enthalpy exceeds
        the upstream value or if CoolProp cannot evaluate the state.
    """
    try:
        density = CP.PropsSI("D", "P", pressure, "S", entropy_upstream, fluid_name)
        enthalpy = CP.PropsSI("H", "P", pressure, "S", entropy_upstream, fluid_name)
    except ValueError:
        return 0.0
    delta_enthalpy = enthalpy_upstream - enthalpy
    if delta_enthalpy <= 0.0:
        return 0.0
    return density * float(np.sqrt(2.0 * delta_enthalpy))
