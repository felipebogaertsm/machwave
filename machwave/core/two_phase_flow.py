import functools
import math
import typing

import numpy as np

if typing.TYPE_CHECKING:
    import machwave.services.coolprop as coolprop_service

DEFAULT_SWEEP_POINTS = 200  # [-]


def get_homogeneous_equilibrium_mass_flux(
    fluid_name: str,
    temperature_upstream: float,
    pressure_downstream: float,
    pressure_upstream: float | None = None,
    sweep_points: int = DEFAULT_SWEEP_POINTS,
    saturated_inlet_flux_maximum: tuple[float, float] | None = None,
) -> float:
    """
    Get the mass flux through an orifice via the homogeneous-equilibrium model.

    Takes the maximum isentropic mass flux over a grid of pressures from downstream
    to upstream. This is the choked mass flux when the orifice is critical, otherwise
    the value at the downstream pressure. The maximum is found by bisection. Where
    CoolProp cannot resolve a state, every grid point is evaluated instead.

    A saturated inlet, at or below the saturation pressure, expands from the
    saturated liquid whatever its pressure, so its grid runs up to the saturation
    pressure, and its maximum can be computed once with
    `get_saturated_inlet_flux_maximum` and passed in for every inlet pressure. An
    inlet below the pressure of the maximum passes the isentropic flux at its own
    pressure.

    Args:
        fluid_name: CoolProp fluid name.
        temperature_upstream: Upstream stagnation temperature [K].
        pressure_downstream: Downstream pressure [Pa].
        pressure_upstream: Upstream stagnation pressure [Pa]. If `None`, the saturation
            pressure at the upstream temperature is used.
        sweep_points: Number of pressure points in the isentropic sweep.
        saturated_inlet_flux_maximum: Result of `get_saturated_inlet_flux_maximum`
            for the same fluid, temperature, downstream pressure and sweep points.
            If `None`, it is computed when the inlet is saturated.

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

    if _is_saturated(coolprop, temperature_upstream, upstream_pressure):
        maximum_flux, maximum_pressure = (
            get_saturated_inlet_flux_maximum(
                fluid_name, temperature_upstream, pressure_downstream, sweep_points
            )
            if saturated_inlet_flux_maximum is None
            else saturated_inlet_flux_maximum
        )
        if upstream_pressure >= maximum_pressure:
            return maximum_flux
        return _get_isentropic_mass_flux(
            coolprop,
            upstream_pressure,
            coolprop.get_saturated_liquid_enthalpy(temperature_upstream),
            coolprop.get_saturated_liquid_entropy(temperature_upstream),
        )

    upstream_enthalpy, upstream_entropy = _get_stagnation_enthalpy_and_entropy(
        coolprop, temperature_upstream, upstream_pressure
    )
    pressures = np.linspace(pressure_downstream, upstream_pressure, sweep_points)
    return _get_isentropic_flux_maximum(
        coolprop, pressures, upstream_enthalpy, upstream_entropy
    )[0]


def get_dyer_mass_flux(
    fluid_name: str,
    temperature_upstream: float,
    density_upstream: float,
    pressure_upstream: float,
    pressure_downstream: float,
    non_equilibrium_factor: float = 1.0,
    saturated_inlet_flux_maximum: tuple[float, float] | None = None,
    vapor_pressure: float | None = None,
) -> float:
    """
    Get the mass flux through an orifice via Dyer's non-equilibrium model.

    Blends the single-phase incompressible flux and the flux of
    `get_homogeneous_equilibrium_mass_flux` by the non-equilibrium parameter. The
    weights follow Waxman et al. The printed Eq. 36 of Dyer et al. swaps them.
    Returns the incompressible flux when nothing can flash in the orifice. That is
    the case when the vapor pressure is at or below the downstream pressure, the inlet
    is at or above the critical temperature, or the inlet is all vapor.
    `non_equilibrium_factor` scales the non-equilibrium parameter to calibrate a long
    orifice, which is closer to equilibrium. An infinite factor returns the
    incompressible flux without any fluid property.
    Verified, not validated against measured flow.

    Args:
        fluid_name: CoolProp fluid name.
        temperature_upstream: Upstream stagnation temperature [K].
        density_upstream: Upstream density, used by the incompressible term
            [kg/m^3].
        pressure_upstream: Upstream stagnation pressure [Pa].
        pressure_downstream: Downstream pressure [Pa].
        non_equilibrium_factor: Multiplier on kappa (dimensionless).
        saturated_inlet_flux_maximum: Passed on to
            `get_homogeneous_equilibrium_mass_flux`.
        vapor_pressure: Saturation pressure at the upstream temperature [Pa]. If
            `None`, it is looked up when needed.

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
    if math.isinf(non_equilibrium_factor):
        return incompressible_mass_flux

    coolprop = coolprop_service.CoolPropService(fluid_name)
    if temperature_upstream >= coolprop.get_critical_temperature():
        return incompressible_mass_flux
    if vapor_pressure is None:
        vapor_pressure = coolprop.get_saturation_pressure(temperature_upstream)
    if (
        vapor_pressure <= pressure_downstream
        or density_upstream
        <= coolprop.get_saturated_vapor_density(temperature_upstream)
    ):
        return incompressible_mass_flux

    non_equilibrium_parameter = non_equilibrium_factor * float(
        np.sqrt(pressure_drop / (vapor_pressure - pressure_downstream))
    )
    equilibrium_mass_flux = get_homogeneous_equilibrium_mass_flux(
        fluid_name=fluid_name,
        temperature_upstream=temperature_upstream,
        pressure_downstream=pressure_downstream,
        pressure_upstream=pressure_upstream,
        saturated_inlet_flux_maximum=saturated_inlet_flux_maximum,
    )
    return (
        non_equilibrium_parameter * incompressible_mass_flux + equilibrium_mass_flux
    ) / (1.0 + non_equilibrium_parameter)


def get_saturated_inlet_flux_maximum(
    fluid_name: str,
    temperature: float,
    pressure_downstream: float,
    sweep_points: int = DEFAULT_SWEEP_POINTS,
) -> tuple[float, float]:
    """
    Get the largest isentropic mass flux from the saturated liquid and its pressure.

    This is the homogeneous-equilibrium flux of every saturated inlet at or above
    that pressure, for the given temperature and downstream pressure.

    Args:
        fluid_name: CoolProp fluid name.
        temperature: Saturation temperature of the inlet [K].
        pressure_downstream: Downstream pressure [Pa].
        sweep_points: Number of pressure points between the downstream and the
            saturation pressure.

    Returns:
        Tuple of mass flux [kg/(m^2-s)] and the pressure it occurs at [Pa].
    """
    import machwave.services.coolprop as coolprop_service

    coolprop = coolprop_service.CoolPropService(fluid_name)
    pressures = np.linspace(
        pressure_downstream, coolprop.get_saturation_pressure(temperature), sweep_points
    )
    return _get_isentropic_flux_maximum(
        coolprop,
        pressures,
        coolprop.get_saturated_liquid_enthalpy(temperature),
        coolprop.get_saturated_liquid_entropy(temperature),
    )


def _get_isentropic_flux_maximum(
    coolprop: "coolprop_service.CoolPropService",
    pressures: np.ndarray,
    enthalpy_upstream: float,
    entropy_upstream: float,
) -> tuple[float, float]:
    """
    Get the largest isentropic mass flux over a pressure grid and its pressure.

    Bisects on the sign of the flux difference between neighbouring points, and
    evaluates every point where a zero or a tie breaks the single-maximum shape.

    Args:
        coolprop: Fluid-property service bound to the working fluid.
        pressures: Increasing pressure grid [Pa].
        enthalpy_upstream: Upstream stagnation enthalpy [J/kg].
        entropy_upstream: Upstream stagnation entropy [J/(kg K)].

    Returns:
        Tuple of mass flux [kg/(m^2-s)] and the grid pressure it occurs at [Pa].
    """

    @functools.cache
    def get_mass_flux(index: int) -> float:
        return _get_isentropic_mass_flux(
            coolprop, pressures[index], enthalpy_upstream, entropy_upstream
        )

    lower_index, upper_index = 0, len(pressures) - 1
    while lower_index < upper_index:
        middle_index = (lower_index + upper_index) // 2
        mass_flux = get_mass_flux(middle_index)
        next_mass_flux = get_mass_flux(middle_index + 1)
        if mass_flux == next_mass_flux or min(mass_flux, next_mass_flux) == 0.0:
            index = max(range(len(pressures)), key=get_mass_flux)
            return get_mass_flux(index), float(pressures[index])
        if mass_flux < next_mass_flux:
            lower_index = middle_index + 1
        else:
            upper_index = middle_index

    return get_mass_flux(lower_index), float(pressures[lower_index])


def _is_saturated(
    coolprop: "coolprop_service.CoolPropService", temperature: float, pressure: float
) -> bool:
    return temperature < coolprop.get_critical_temperature() and (
        pressure <= coolprop.get_saturation_pressure(temperature)
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
    if not _is_saturated(coolprop, temperature, pressure):
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
