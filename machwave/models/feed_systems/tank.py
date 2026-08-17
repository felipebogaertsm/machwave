import dataclasses
import functools

import machwave.services.coolprop as coolprop_service


@dataclasses.dataclass(frozen=True, slots=True)
class TankFluidState:
    """
    The fluid in a tank at one mass and internal energy.

    Attributes:
        temperature: Fluid temperature [K].
        pressure: Tank pressure [Pa].
        saturated_liquid_density: Saturated liquid density at the temperature [kg/m^3].
        saturated_vapor_density: Saturated vapor density at the temperature [kg/m^3].
    """

    temperature: float
    pressure: float
    saturated_liquid_density: float
    saturated_vapor_density: float


class Tank:
    """
    A generic two-phase tank model for any single fluid recognized by CoolProp.

    This is a static description of the tank: it carries no propellant state.
    Pressure and density are pure functions of the state passed in by the
    caller, which lets the integrator own that state and keeps the model
    re-runnable.

    An isothermal tank is a pure function of the fluid mass. Its temperature is
    held where it was loaded, so a self-pressurizing tank holds its saturation
    pressure flat for as long as any liquid remains.

    A tank running an energy balance is a function of the fluid mass and of the
    internal energy the integrator carries alongside it. Draining takes enthalpy
    out with the fluid, the fluid left behind cools as it boils to refill the
    ullage, and the saturation pressure follows the temperature down over the
    burn.

    Assumptions:
      - Two-phase equilibrium if there's enough mass to form liquid + vapor.
      - If insufficient mass for liquid, treat it as single-phase vapor via
        the real-gas equation of state.
      - Nothing crosses the tank wall: no heat in, and no work other than what
        the leaving fluid carries.
    """

    def __init__(
        self,
        fluid_name: str,
        volume: float,
        temperature: float,
        initial_fluid_mass: float,
        overfill_tolerance: float = 0.01,
        isothermal: bool = True,
    ) -> None:
        """
        Initialize a two-phase tank model.

        Args:
            fluid_name: Name of the fluid in the CoolProp database.
            volume: Internal volume of the tank [m^3] (>0).
            temperature: Absolute temperature [K] the tank is loaded at (>0).
                An isothermal tank stays there; a tank running an energy
                balance starts there and cools from it.
            initial_fluid_mass: Initial total mass of fluid [kg] (>=0). This is
                the tank's loading; the integrator owns the mass thereafter.
            overfill_tolerance: Allowed fraction over the saturated liquid
                density, e.g. 0.01 = 1% (>=0).
            isothermal: Whether the temperature is held where the tank was
                loaded. False runs an energy balance instead, and every query
                then needs the internal energy the integrator carries beside
                the mass, starting from `initial_internal_energy`.

        Raises:
            ValueError: If the fluid is unknown to CoolProp, if any argument is
                outside its valid physical range, or if the initial fill is
                denser than the saturated liquid.
        """
        self.fluid_name = fluid_name
        self.volume = volume
        self.temperature = temperature
        self.initial_fluid_mass = initial_fluid_mass
        self.overfill_tolerance = overfill_tolerance
        self.isothermal = isothermal

        self._coolprop = coolprop_service.CoolPropService(fluid_name)

        self._validate()

        # The tank is isothermal with a fixed fluid, so these properties are constant
        # and cached
        self.saturation_pressure = self._coolprop.get_saturation_pressure(temperature)
        self.saturated_liquid_density = self._coolprop.get_saturated_liquid_density(
            temperature
        )
        self.saturated_vapor_density = self._coolprop.get_saturated_vapor_density(
            temperature
        )
        # Vapor pressure at the tank temperature, memoized per fluid mass.
        self._pressure_by_mass: dict[float, float] = {}
        # Energy balance state, memoized per fluid mass and internal energy.
        self._fluid_state_by_state: dict[tuple[float, float], TankFluidState] = {}

        self._check_not_overfilled()

    def _validate(self) -> None:
        """
        Validate the scalar tank inputs.

        Raises:
            ValueError: If any field is outside its valid physical range.
        """
        if self.volume <= 0.0:
            raise ValueError(f"volume must be strictly positive, got {self.volume}")
        if self.temperature <= 0.0:
            raise ValueError(
                f"temperature must be strictly positive, got {self.temperature}"
            )
        if self.initial_fluid_mass < 0.0:
            raise ValueError(
                "initial_fluid_mass must be non-negative, got "
                f"{self.initial_fluid_mass}"
            )
        if self.overfill_tolerance < 0.0:
            raise ValueError(
                "overfill_tolerance must be non-negative, got "
                f"{self.overfill_tolerance}"
            )

        self._validate_temperature_range()

    def _validate_temperature_range(self) -> None:
        """
        Validate the temperature against the two-phase range of the fluid.

        The range spans the triple point up to, but not including, the critical
        temperature: at and above the critical point the liquid and vapor phases
        are no longer distinct, so the saturation model does not hold.

        Raises:
            ValueError: If the fluid is unknown to CoolProp, or if the
                temperature lies outside the two-phase range of the fluid.
        """
        try:
            triple_point_temperature = self._coolprop.get_triple_point_temperature()
            critical_temperature = self._coolprop.get_critical_temperature()
        except ValueError as error:
            raise ValueError(
                "fluid_name must be a fluid recognized by CoolProp, got "
                f"{self.fluid_name!r}"
            ) from error

        if not triple_point_temperature <= self.temperature < critical_temperature:
            raise ValueError(
                f"temperature {self.temperature} K is outside the two-phase range "
                f"of {self.fluid_name}, which spans {triple_point_temperature} K "
                f"(triple point) up to but excluding {critical_temperature} K "
                f"(critical point)"
            )

    def _check_not_overfilled(self) -> None:
        """
        Check whether the tank is overfilled within the `overfill_tolerance` threshold.

        Raises:
            ValueError: If the bulk density exceeds the saturated liquid density.
        """
        bulk_density = self.initial_fluid_mass / self.volume

        if bulk_density > self.saturated_liquid_density * (1 + self.overfill_tolerance):
            raise ValueError(
                f"Tank overfilled: bulk density {bulk_density:.1f} kg/m^3 exceeds "
                f"liquid density {self.saturated_liquid_density:.1f} kg/m^3 for "
                f"{self.fluid_name} at {self.temperature} K"
            )

    @functools.cached_property
    def initial_internal_energy(self) -> float:
        """
        Internal energy of the fluid the tank is loaded with [J].

        Where a tank running an energy balance starts. The integrator carries
        it from here, taking out the enthalpy of whatever leaves.
        """
        if self.initial_fluid_mass <= 0.0:
            return 0.0

        return (
            self._coolprop.get_internal_energy_at_temperature_density(
                self.temperature, self.initial_fluid_mass / self.volume
            )
            * self.initial_fluid_mass
        )

    def _get_fluid_state(
        self, fluid_mass: float, internal_energy: float | None
    ) -> TankFluidState:
        """
        Resolve the fluid at a mass and internal energy, memoized on the pair.

        The bulk density and the specific internal energy fix the state, and
        the temperature that comes out of it fixes the saturation densities the
        fill state is read against.

        Raises:
            ValueError: If no internal energy was given, or if the fluid has
                left the range CoolProp holds it over.
        """
        if internal_energy is None:
            raise ValueError(
                "A tank running an energy balance needs the internal energy of "
                "its fluid alongside the mass; it starts at "
                "initial_internal_energy."
            )

        memo_key = (fluid_mass, internal_energy)
        fluid_state = self._fluid_state_by_state.get(memo_key)
        if fluid_state is not None:
            return fluid_state

        density = fluid_mass / self.volume
        specific_internal_energy = internal_energy / fluid_mass
        try:
            temperature = self._coolprop.get_temperature_at_density_internal_energy(
                density, specific_internal_energy
            )
            fluid_state = TankFluidState(
                temperature=temperature,
                pressure=self._coolprop.get_pressure_at_density_internal_energy(
                    density, specific_internal_energy
                ),
                saturated_liquid_density=(
                    self._coolprop.get_saturated_liquid_density(temperature)
                ),
                saturated_vapor_density=(
                    self._coolprop.get_saturated_vapor_density(temperature)
                ),
            )
        except ValueError as error:
            raise ValueError(
                f"{self.fluid_name} at {density:.3f} kg/m^3 and "
                f"{specific_internal_energy:.1f} J/kg is outside the range "
                "CoolProp holds it over; the tank has drained or cooled past "
                "what the two-phase model covers."
            ) from error

        self._fluid_state_by_state[memo_key] = fluid_state
        return fluid_state

    def get_temperature(
        self, fluid_mass: float, internal_energy: float | None = None
    ) -> float:
        """
        Return the fluid temperature [K].

        An isothermal tank stays where it was loaded. A tank running an energy
        balance follows its fluid down as the fluid boils to refill the ullage.

        Args:
            fluid_mass: Current total mass of fluid in the tank [kg].
            internal_energy: Current internal energy of that fluid [J].
                Required for a tank running an energy balance, unused
                otherwise.

        Returns:
            Fluid temperature [K].
        """
        if self.isothermal or fluid_mass <= 0:
            return self.temperature

        return self._get_fluid_state(fluid_mass, internal_energy).temperature

    def is_delivering_liquid(
        self, fluid_mass: float, internal_energy: float | None = None
    ) -> bool:
        """
        Whether the tank still holds liquid to feed, rather than vapor alone.

        True while the fluid mass exceeds the mass of saturated vapor that
        fills the tank, which is where the two-phase equilibrium holds.

        Args:
            fluid_mass: Current total mass of fluid in the tank [kg].
            internal_energy: Current internal energy of that fluid [J].
                Required for a tank running an energy balance, unused
                otherwise.

        Returns:
            True if liquid remains in the tank.
        """
        if self.isothermal:
            saturated_vapor_density = self.saturated_vapor_density
        else:
            saturated_vapor_density = self._get_fluid_state(
                fluid_mass, internal_energy
            ).saturated_vapor_density

        return fluid_mass > saturated_vapor_density * self.volume

    def get_pressure(
        self, fluid_mass: float, internal_energy: float | None = None
    ) -> float:
        """
        Return the tank pressure [Pa] for a given fluid state.

        1) An empty tank has zero pressure.
        2) If the fluid mass exceeds the mass of saturated vapor that fills the tank,
            the tank is partially liquid and the pressure is the saturation pressure.
        3) Otherwise, the tank is all sub-saturated vapor and the pressure follows the
            real-gas equation of state at the bulk density. This matches the saturation
            pressure at the phase boundary, so pressure stays continuous as the tank
            crosses out of the two-phase regime.

        A tank running an energy balance reads both off the state its mass and
        internal energy fix, which walks the saturation pressure down with the
        temperature instead of holding it flat.

        Args:
            fluid_mass: Current total mass of fluid in the tank [kg].
            internal_energy: Current internal energy of that fluid [J].
                Required for a tank running an energy balance, unused
                otherwise.

        Returns:
            Tank pressure [Pa].
        """
        if fluid_mass <= 0:
            return 0.0

        if not self.isothermal:
            return self._get_fluid_state(fluid_mass, internal_energy).pressure

        if self.is_delivering_liquid(fluid_mass):
            return self.saturation_pressure

        if fluid_mass not in self._pressure_by_mass:
            self._pressure_by_mass[fluid_mass] = (
                self._coolprop.get_pressure_at_temperature_density(
                    self.temperature, fluid_mass / self.volume
                )
            )
        return self._pressure_by_mass[fluid_mass]

    def get_outflow_specific_enthalpy(
        self, fluid_mass: float, internal_energy: float | None = None
    ) -> float:
        """
        Return the specific enthalpy of the fluid leaving the tank [J/kg].

        What the energy balance takes out per unit mass drained. The feed
        system draws liquid from the bottom while any remains, and vapor at the
        bulk state once none does, so this steps up by the latent heat as the
        last of the liquid goes.

        Args:
            fluid_mass: Current total mass of fluid in the tank [kg].
            internal_energy: Current internal energy of that fluid [J].
                Required for a tank running an energy balance, unused
                otherwise.

        Returns:
            Specific enthalpy of the leaving fluid [J/kg].
        """
        if fluid_mass <= 0:
            return 0.0

        temperature = self.get_temperature(fluid_mass, internal_energy)
        if self.is_delivering_liquid(fluid_mass, internal_energy):
            return self._coolprop.get_saturated_liquid_enthalpy(temperature)

        return self._coolprop.get_enthalpy_at_temperature_density(
            temperature, fluid_mass / self.volume
        )

    def get_density(
        self, fluid_mass: float, internal_energy: float | None = None
    ) -> float:
        """
        Return fluid density [kg/m^3] for a given fluid state.

        1) An empty tank has zero density.
        2) Otherwise the fill state fixes the density: a partially liquid tank returns
            the saturated liquid density (the feed system pulls liquid from the bottom),
            and an all-vapor tank returns the bulk density.

        Args:
            fluid_mass: Current total mass of fluid in the tank [kg].
            internal_energy: Current internal energy of that fluid [J].
                Required for a tank running an energy balance, unused
                otherwise.

        Returns:
            Fluid density [kg/m^3].
        """
        if fluid_mass <= 0:
            return 0.0

        if not self.is_delivering_liquid(fluid_mass, internal_energy):
            return fluid_mass / self.volume

        if self.isothermal:
            return self.saturated_liquid_density
        return self._get_fluid_state(
            fluid_mass, internal_energy
        ).saturated_liquid_density
