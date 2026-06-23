import machwave.services.coolprop as coolprop_service


class Tank:
    """
    A generic two-phase tank model for any single fluid recognized by CoolProp.

    This is a static description of the tank: it carries no propellant-mass
    state. Pressure and density are pure functions of a fluid mass passed in by
    the caller, which lets the integrator own the mass and keeps the model
    re-runnable.

    Assumptions:
      - Constant temperature (isothermal).
      - Two-phase equilibrium if there's enough mass to form liquid + vapor.
      - If insufficient mass for liquid, treat it as single-phase vapor via
        the real-gas equation of state.
      - Ignores temperature changes upon phase change (no thermal balance).
    """

    def __init__(
        self,
        fluid_name: str,
        volume: float,
        temperature: float,
        initial_fluid_mass: float,
        overfill_tolerance: float = 0.01,
    ) -> None:
        """
        Initialize a two-phase tank model.

        Args:
            fluid_name: Name of the fluid in the CoolProp database.
            volume: Internal volume of the tank [m^3] (>0).
            temperature: Absolute temperature [K], assumed constant (>0).
            initial_fluid_mass: Initial total mass of fluid [kg] (>=0). This is
                the tank's loading; the integrator owns the mass thereafter.
            overfill_tolerance: Allowed fraction over the saturated liquid
                density, e.g. 0.01 = 1% (>=0).

        Raises:
            ValueError: If any argument is outside its valid physical range, or
                if the initial fill is denser than the saturated liquid.
        """
        self.fluid_name = fluid_name
        self.volume = volume
        self.temperature = temperature
        self.initial_fluid_mass = initial_fluid_mass
        self.overfill_tolerance = overfill_tolerance

        self._validate()

        self._coolprop = coolprop_service.CoolPropService(fluid_name)

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

    def get_pressure(self, fluid_mass: float) -> float:
        """
        Return the tank pressure [Pa] for a given fluid mass.

        1) An empty tank has zero pressure.
        2) If the fluid mass exceeds the mass of saturated vapor that fills the
            tank, the tank is partially liquid and the pressure is the saturation
            pressure.
        3) Otherwise, the tank is all sub-saturated vapor and the pressure
            follows the real-gas equation of state at the bulk density. This
            matches the saturation pressure at the phase boundary, so pressure
            stays continuous as the tank crosses out of the two-phase regime.

        Args:
            fluid_mass: Current total mass of fluid in the tank [kg].

        Returns:
            Tank pressure [Pa].
        """
        if fluid_mass <= 0:
            return 0.0

        if fluid_mass > self.saturated_vapor_density * self.volume:
            return self.saturation_pressure

        if fluid_mass not in self._pressure_by_mass:
            self._pressure_by_mass[fluid_mass] = (
                self._coolprop.get_pressure_at_temperature_density(
                    self.temperature, fluid_mass / self.volume
                )
            )
        return self._pressure_by_mass[fluid_mass]

    def get_density(self, fluid_mass: float) -> float:
        """
        Return fluid density [kg/m^3] for a given fluid mass.

        1) An empty tank has zero density.
        2) Otherwise the fill state fixes the density: a partially liquid tank
            returns the saturated liquid density (the feed system pulls liquid
            from the bottom), and an all-vapor tank returns the bulk density.

        Args:
            fluid_mass: Current total mass of fluid in the tank [kg].

        Returns:
            Fluid density [kg/m^3].
        """
        if fluid_mass <= 0:
            return 0.0

        if fluid_mass > self.saturated_vapor_density * self.volume:
            return self.saturated_liquid_density
        return fluid_mass / self.volume
