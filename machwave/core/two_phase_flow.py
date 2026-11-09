import functools
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

    Takes the maximum isentropic mass flux over a grid of pressures from downstream
    to upstream: the choked mass flux when the orifice is critical, otherwise the
    value at the downstream pressure. Along the isentrope the flux rises from zero
    at the upstream pressure to a single maximum, so the grid maximum is found by
    bisecting on the sign of the flux difference between neighbouring points. The
    flux is zero where CoolProp cannot resolve the state (single points near the
    critical temperature, all points below the triple point), which breaks that
    shape, so a zero or a tie between neighbours falls back to evaluating every
    point.

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

    @functools.cache
    def get_mass_flux(index: int) -> float:
        return _get_isentropic_mass_flux(
            coolprop, pressures[index], upstream_enthalpy, upstream_entropy
        )

    lower_index, upper_index = 0, sweep_points - 1
    while lower_index < upper_index:
        middle_index = (lower_index + upper_index) // 2
        mass_flux = get_mass_flux(middle_index)
        next_mass_flux = get_mass_flux(middle_index + 1)
        if mass_flux == next_mass_flux or min(mass_flux, next_mass_flux) == 0.0:
            return max(get_mass_flux(index) for index in range(sweep_points))
        if mass_flux < next_mass_flux:
            lower_index = middle_index + 1
        else:
            upper_index = middle_index

    return get_mass_flux(lower_index)


def get_dyer_mass_flux(
    fluid_name: str,
    temperature_upstream: float,
    density_upstream: float,
    pressure_upstream: float,
    pressure_downstream: float,
) -> float:
    """
    Get the mass flux through an orifice via Dyer's non-equilibrium model.

    Dyer's non-homogeneous non-equilibrium (NHNE) model blends the
    single-phase incompressible flux and the homogeneous-equilibrium flux by
    the non-equilibrium parameter kappa, the square root of the ratio of
    bubble growth time to liquid residence time:

        G = kappa / (1 + kappa) * G_SPI + 1 / (1 + kappa) * G_HEM
        kappa = sqrt((P1 - P2) / (Pv - P2))

    with Pv the vapor pressure at the upstream temperature (Dyer et al. 2007,
    Eqs. 35 to 37). Bubbles that grow slowly against the residence time
    (large kappa) leave the liquid no time to flash, so the flux tends to SPI;
    fast growth tends to HEM. The weights follow that limit, which Dyer et al.
    state on p. 10; their Eq. 36 as printed puts 1 / (1 + kappa) on SPI instead,
    and later work (Waxman et al. 2013, Eq. 9) uses the form here. The orifice
    length drops out with the constants of the two time scales, so the model
    has no L/D dependence. G_HEM is the choked or unchoked flux of
    `get_homogeneous_equilibrium_mass_flux` over [P2, P1].

    Valid for a liquid inlet below the critical temperature with Pv > P2. The
    inlet may be subcooled (P1 >= Pv, kappa >= 1) or below its own vapor
    pressure after a line loss (P1 < Pv, kappa < 1); kappa is continuous
    through P1 = Pv. Where nothing can flash in the orifice (Pv <= P2, an
    upstream temperature at or above the critical temperature, or an all-vapor
    inlet at or below the saturated vapor density) the flux is the SPI flux,
    the kappa -> infinity limit.

    Verified against the closed form and its SPI and HEM limits, not
    validated against measured orifice flows.

    References:
        Dyer, J., Doran, E., Dunn, Z., Lohner, K., Zilliac, G., and Cantwell,
        B., "Modeling Feed System Flow Physics for Self-Pressurizing
        Propellants", AIAA 2007-5702, 2007.
        Waxman, B. S., Zimmerman, J. E., Cantwell, B. J., and Zilliac, G. G.,
        "Mass Flow Rate and Isolation Characteristics of Injectors for Use with
        Self-Pressurizing Oxidizers in Hybrid Rockets", AIAA 2013-3636, 2013.

    Args:
        fluid_name: CoolProp fluid name.
        temperature_upstream: Upstream stagnation temperature [K].
        density_upstream: Upstream density, used by the SPI term [kg/m^3].
        pressure_upstream: Upstream stagnation pressure [Pa].
        pressure_downstream: Downstream pressure [Pa].

    Returns:
        Mass flux [kg/(m^2-s)]. Zero if the downstream pressure is at or above
        the upstream pressure.

    Raises:
        MissingOptionalDependencyError: If the `liquid` extra is not installed.
    """
    import machwave.services.coolprop as coolprop_service

    if pressure_downstream >= pressure_upstream:
        return 0.0

    pressure_drop = pressure_upstream - pressure_downstream
    spi_mass_flux = float(np.sqrt(2.0 * density_upstream * pressure_drop))

    coolprop = coolprop_service.CoolPropService(fluid_name)
    if temperature_upstream >= coolprop.get_critical_temperature():
        return spi_mass_flux
    vapor_pressure = coolprop.get_saturation_pressure(temperature_upstream)
    if (
        vapor_pressure <= pressure_downstream
        or density_upstream
        <= coolprop.get_saturated_vapor_density(temperature_upstream)
    ):
        return spi_mass_flux

    non_equilibrium_parameter = float(
        np.sqrt(pressure_drop / (vapor_pressure - pressure_downstream))
    )
    hem_mass_flux = get_homogeneous_equilibrium_mass_flux(
        fluid_name=fluid_name,
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
        pressure_upstream=pressure_upstream,
    )
    return (non_equilibrium_parameter * spi_mass_flux + hem_mass_flux) / (
        1.0 + non_equilibrium_parameter
    )


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
        density, enthalpy = coolprop.get_density_and_enthalpy_at_pressure_entropy(
            pressure, entropy_upstream
        )
    except ValueError:
        return 0.0
    delta_enthalpy = enthalpy_upstream - enthalpy
    if delta_enthalpy <= 0.0:
        return 0.0
    return density * float(np.sqrt(2.0 * delta_enthalpy))
