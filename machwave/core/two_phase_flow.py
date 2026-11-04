import functools
import typing

import numpy as np
import scipy.optimize as scipy_optimize

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

    Dyer's non-homogeneous non-equilibrium (NHNE) model blends the
    single-phase incompressible flux and the critical homogeneous-equilibrium
    flux by the ratio of bubble growth time to liquid residence time:

        G = kappa / (1 + kappa) * G_SPI + 1 / (1 + kappa) * G_HEM
        kappa = sqrt((P1 - P2) / (Pv - P2))

    with Pv the vapor pressure at the upstream temperature (Dyer et al. 2007,
    Eqs. 35 to 37). Bubbles that grow slowly against the residence time
    (large kappa) leave the liquid no time to flash, so the flux tends to SPI;
    fast growth tends to HEM. The weights follow that limit, which Dyer et al.
    state on p. 10; their Eq. 36 as printed puts 1 / (1 + kappa) on SPI instead,
    and later work (Waxman et al. 2013, Eq. 9) uses the form here. The orifice
    length drops out with the constants of the two time scales, so the model
    has no L/D dependence.

    References:
        Dyer, J., Doran, E., Dunn, Z., Lohner, K., Zilliac, G., and Cantwell,
        B., "Modeling Feed System Flow Physics for Self-Pressurizing
        Propellants", AIAA 2007-5702, 2007.

    Edge cases:
        - P1 <= P2: no flow.
        - Pv <= P2, an upstream temperature at or above the critical point, or
          an all-vapor inlet (density at or below the saturated vapor density):
          nothing can flash in the orifice, so the flux is pure SPI (the
          kappa -> infinity limit).
        - P1 >= Pv (subcooled inlet): kappa >= 1, the formula holds as is.
        - P1 < Pv (inlet below its own vapor pressure, as after a line loss on
          a saturated tank): kappa < 1, the formula holds as is. The time-scale
          ratio only needs P1 > P2 and Pv > P2, and kappa is continuous through
          P1 = Pv.

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
    if pressure_downstream >= pressure_upstream:
        return 0.0

    pressure_drop = pressure_upstream - pressure_downstream
    spi_mass_flux = float(np.sqrt(2.0 * density_upstream * pressure_drop))

    saturation = _get_saturation_state(fluid_name, temperature_upstream)
    if saturation is None:
        return spi_mass_flux
    vapor_pressure, saturated_vapor_density = saturation
    if (
        vapor_pressure <= pressure_downstream
        or density_upstream <= saturated_vapor_density
    ):
        return spi_mass_flux

    kappa = float(np.sqrt(pressure_drop / (vapor_pressure - pressure_downstream)))
    hem_mass_flux = _get_critical_homogeneous_equilibrium_mass_flux(
        fluid_name, temperature_upstream, pressure_upstream, pressure_downstream
    )
    return (kappa * spi_mass_flux + hem_mass_flux) / (1.0 + kappa)


@functools.lru_cache(maxsize=256)
def _get_saturation_state(
    fluid_name: str, temperature: float
) -> tuple[float, float] | None:
    """
    Get the vapor pressure and saturated vapor density at a temperature.

    Memoized on the exact temperature: an isothermal tank holds it fixed.

    Args:
        fluid_name: CoolProp fluid name.
        temperature: Temperature [K].

    Returns:
        Tuple of vapor pressure [Pa] and saturated vapor density [kg/m^3], or
        `None` at or above the critical temperature, where the fluid has no
        vapor pressure.
    """
    coolprop = _get_coolprop_service(fluid_name)
    critical_temperature, _ = _get_fluid_limits(fluid_name)
    if temperature >= critical_temperature:
        return None
    return (
        coolprop.get_saturation_pressure(temperature),
        coolprop.get_saturated_vapor_density(temperature),
    )


def _get_critical_homogeneous_equilibrium_mass_flux(
    fluid_name: str,
    temperature_upstream: float,
    pressure_upstream: float,
    pressure_downstream: float,
) -> float:
    """
    Get the HEM mass flux, choked below the critical pressure.

    The same quantity as `get_homogeneous_equilibrium_mass_flux`, the maximum of
    the isentropic flux over [P2, P1], found from the critical point instead of
    a sweep. A simulation calls this hundreds of times per inlet state, and the
    sweep costs 200 property calls each time.

    Args:
        fluid_name: CoolProp fluid name.
        temperature_upstream: Upstream stagnation temperature [K].
        pressure_upstream: Upstream stagnation pressure [Pa].
        pressure_downstream: Downstream pressure [Pa].

    Returns:
        Mass flux [kg/(m^2-s)].
    """
    saturation = _get_saturation_state(fluid_name, temperature_upstream)
    vapor_pressure = None if saturation is None else saturation[0]
    # Below its vapor pressure the inlet is read as saturated liquid, so the
    # stagnation state, and the critical point with it, does not depend on P1.
    stagnation_pressure = (
        pressure_upstream
        if vapor_pressure is None or pressure_upstream > vapor_pressure
        else vapor_pressure
    )
    critical_pressure, critical_mass_flux, _, _ = _get_critical_point(
        fluid_name, temperature_upstream, stagnation_pressure
    )

    # The isentropic flux rises from zero at the stagnation pressure to its peak
    # at the critical pressure, then falls, so its maximum over [P2, P1] is at
    # the critical pressure clipped into that interval.
    pressure = min(max(critical_pressure, pressure_downstream), pressure_upstream)
    if pressure == critical_pressure:
        return critical_mass_flux
    return _get_unchoked_mass_flux(
        fluid_name, temperature_upstream, stagnation_pressure, pressure
    )


@functools.lru_cache(maxsize=256)
def _get_unchoked_mass_flux(
    fluid_name: str,
    temperature: float,
    stagnation_pressure: float,
    pressure: float,
) -> float:
    """
    Get the isentropic flux at a pressure above the critical one.

    Memoized on the exact arguments, so a hit returns the very same value. The
    feedline solve evaluates the element at several inlet pressures against
    one chamber pressure; from a saturated tank the stagnation state does not
    move with the inlet pressure, so most of those calls repeat one of these
    keys (84 % on the 1 kN test engine).

    Args:
        fluid_name: CoolProp fluid name.
        temperature: Stagnation temperature [K].
        stagnation_pressure: Stagnation pressure [Pa].
        pressure: Pressure the flux is taken at [Pa].

    Returns:
        Mass flux [kg/(m^2-s)].
    """
    _, _, enthalpy, entropy = _get_critical_point(
        fluid_name, temperature, stagnation_pressure
    )
    return _get_isentropic_mass_flux(
        _get_coolprop_service(fluid_name), pressure, enthalpy, entropy
    )


@functools.lru_cache(maxsize=256)
def _get_critical_point(
    fluid_name: str, temperature: float, pressure: float
) -> tuple[float, float, float, float]:
    """
    Locate the HEM critical point for a stagnation state.

    Memoized on the exact stagnation state: a simulation step holds the inlet
    fixed while the solver tries many chamber pressures.

    Args:
        fluid_name: CoolProp fluid name.
        temperature: Stagnation temperature [K].
        pressure: Stagnation pressure [Pa].

    Returns:
        Tuple of critical pressure [Pa], critical mass flux [kg/(m^2-s)],
        stagnation enthalpy [J/kg] and stagnation entropy [J/(kg K)].
    """
    coolprop = _get_coolprop_service(fluid_name)
    enthalpy, entropy = _get_stagnation_enthalpy_and_entropy(
        coolprop, temperature, pressure
    )
    _, lowest_pressure = _get_fluid_limits(fluid_name)
    result = scipy_optimize.minimize_scalar(
        lambda p: -_get_isentropic_mass_flux(coolprop, p, enthalpy, entropy),
        bounds=(lowest_pressure, pressure),
        method="bounded",
        options={"xatol": 1e-6 * pressure},
    )
    return float(result.x), float(-result.fun), enthalpy, entropy


@functools.lru_cache(maxsize=8)
def _get_coolprop_service(fluid_name: str) -> "coolprop_service.CoolPropService":
    """
    Get one property service per fluid for the HEM flux.

    The service keeps a CoolProp `AbstractState` that each (P, s) flash
    overwrites in full, so sharing it does not make a result depend on the
    calls before it.

    Args:
        fluid_name: CoolProp fluid name.

    Returns:
        Fluid-property service bound to the fluid.
    """
    import machwave.services.coolprop as coolprop_service

    return coolprop_service.CoolPropService(fluid_name)


@functools.lru_cache(maxsize=8)
def _get_fluid_limits(fluid_name: str) -> tuple[float, float]:
    """
    Get the critical temperature and the triple point pressure of a fluid.

    Args:
        fluid_name: CoolProp fluid name.

    Returns:
        Tuple of critical temperature [K] and saturation pressure at the
        triple point temperature [Pa].
    """
    coolprop = _get_coolprop_service(fluid_name)
    return (
        coolprop.get_critical_temperature(),
        coolprop.get_saturation_pressure(coolprop.get_triple_point_temperature()),
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
    critical_temperature, _ = _get_fluid_limits(coolprop.fluid_name)
    is_saturated = temperature < critical_temperature and (
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
