import typing

import numpy as np

if typing.TYPE_CHECKING:
    import machwave.services.coolprop as coolprop_service


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
        MissingOptionalDependencyError: If the `liquid` extra is not installed.
    """
    import machwave.services.coolprop as coolprop_service

    if sweep_points < 2:
        raise ValueError("sweep_points must be at least 2")

    coolprop = coolprop_service.CoolPropService(fluid_name)

    upstream_pressure = (
        coolprop.get_saturation_pressure(temperature_upstream)
        if pressure_upstream is None
        else pressure_upstream
    )

    if pressure_downstream >= upstream_pressure:
        return 0.0

    upstream_enthalpy, upstream_entropy = _get_stagnation_enthalpy_and_entropy(
        coolprop, temperature_upstream, upstream_pressure
    )

    pressures = np.linspace(pressure_downstream, upstream_pressure, sweep_points)
    mass_flux = np.zeros_like(pressures)
    for index, pressure in enumerate(pressures):
        mass_flux[index] = _get_isentropic_mass_flux(
            coolprop, pressure, upstream_enthalpy, upstream_entropy
        )

    return float(mass_flux.max())


def get_dyer_mass_flux(
    fluid_name: str,
    temperature_upstream: float,
    density_upstream: float,
    pressure_upstream: float,
    pressure_downstream: float,
) -> float:
    """
    Get the mass flux through an orifice via Dyer's non-equilibrium model.

    Blends the single-phase incompressible flux and the flux of
    `get_homogeneous_equilibrium_mass_flux` by the non-equilibrium parameter. The
    weights follow Waxman et al.; Eq. 36 of Dyer et al. as printed swaps them. Where
    nothing can flash in the orifice (vapor pressure at or below the downstream
    pressure, an inlet at or above the critical temperature, or an all-vapor inlet),
    the incompressible flux is returned.

    Args:
        fluid_name: CoolProp fluid name.
        temperature_upstream: Upstream stagnation temperature [K].
        density_upstream: Upstream density, used by the incompressible term
            [kg/m^3].
        pressure_upstream: Upstream stagnation pressure [Pa].
        pressure_downstream: Downstream pressure [Pa].

    Returns:
        Mass flux [kg/(m^2-s)]. Zero if the downstream pressure is at or above
        the upstream pressure.

    Raises:
        MissingOptionalDependencyError: If the `liquid` extra is not installed.

    References:
        Dyer, J., Doran, E., Dunn, Z., Lohner, K., Zilliac, G., and Cantwell,
        B., "Modeling Feed System Flow Physics for Self-Pressurizing
        Propellants", AIAA 2007-5702, 2007, Eqs. 35 to 37.
        Waxman, B. S., Zimmerman, J. E., Cantwell, B. J., and Zilliac, G. G.,
        "Mass Flow Rate and Isolation Characteristics of Injectors for Use with
        Self-Pressurizing Oxidizers in Hybrid Rockets", AIAA 2013-3636, 2013,
        Eq. 9.
    """
    import machwave.services.coolprop as coolprop_service

    if pressure_downstream >= pressure_upstream:
        return 0.0

    pressure_drop = pressure_upstream - pressure_downstream
    incompressible_mass_flux = float(np.sqrt(2.0 * density_upstream * pressure_drop))

    coolprop = coolprop_service.CoolPropService(fluid_name)
    if temperature_upstream >= coolprop.get_critical_temperature():
        return incompressible_mass_flux
    vapor_pressure = coolprop.get_saturation_pressure(temperature_upstream)
    if (
        vapor_pressure <= pressure_downstream
        or density_upstream
        <= coolprop.get_saturated_vapor_density(temperature_upstream)
    ):
        return incompressible_mass_flux

    non_equilibrium_parameter = float(
        np.sqrt(pressure_drop / (vapor_pressure - pressure_downstream))
    )
    equilibrium_mass_flux = get_homogeneous_equilibrium_mass_flux(
        fluid_name=fluid_name,
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
        pressure_upstream=pressure_upstream,
    )
    return (
        non_equilibrium_parameter * incompressible_mass_flux + equilibrium_mass_flux
    ) / (1.0 + non_equilibrium_parameter)


def _get_stagnation_enthalpy_and_entropy(
    coolprop: "coolprop_service.CoolPropService",
    temperature: float,
    pressure: float,
) -> tuple[float, float]:
    """
    Get enthalpy and entropy at a given pressure and temperature.

    Uses the saturated-liquid state at the requested temperature when the pressure
    is at or below saturation or the pressure-temperature lookup fails.

    Args:
        coolprop: Fluid-property service bound to the working fluid.
        temperature: Stagnation temperature [K].
        pressure: Stagnation pressure [Pa].

    Returns:
        Tuple of enthalpy [J/kg] and entropy [J/(kg K)].
    """
    is_saturated = temperature < coolprop.get_critical_temperature() and (
        pressure <= coolprop.get_saturation_pressure(temperature)
    )
    if not is_saturated:
        try:
            enthalpy = coolprop.get_enthalpy_at_temperature_pressure(
                temperature, pressure
            )
            entropy = coolprop.get_entropy_at_temperature_pressure(
                temperature, pressure
            )
            return enthalpy, entropy
        except ValueError:
            pass

    enthalpy = coolprop.get_saturated_liquid_enthalpy(temperature)
    entropy = coolprop.get_saturated_liquid_entropy(temperature)
    return enthalpy, entropy


def _get_isentropic_mass_flux(
    coolprop: "coolprop_service.CoolPropService",
    pressure: float,
    enthalpy_upstream: float,
    entropy_upstream: float,
) -> float:
    """
    Get the isentropic mass flux at a given pressure for a known upstream state.

    Args:
        coolprop: Fluid-property service bound to the working fluid.
        pressure: Downstream pressure [Pa].
        enthalpy_upstream: Upstream stagnation enthalpy [J/kg].
        entropy_upstream: Upstream stagnation entropy [J/(kg K)].

    Returns:
        Mass flux [kg/(m^2-s)]. Zero if the downstream enthalpy exceeds
        the upstream value or if CoolProp cannot evaluate the state.
    """
    try:
        density = coolprop.get_density_at_pressure_entropy(pressure, entropy_upstream)
        enthalpy = coolprop.get_enthalpy_at_pressure_entropy(pressure, entropy_upstream)
    except ValueError:
        return 0.0
    delta_enthalpy = enthalpy_upstream - enthalpy
    if delta_enthalpy <= 0.0:
        return 0.0
    return density * float(np.sqrt(2.0 * delta_enthalpy))
