import CoolProp.CoolProp as CP

import machwave.core.ideal_gas as ideal_gas


class Tank:
    """
    A generic two-phase tank model for any single fluid recognized by CoolProp.

    Assumptions:
      - Constant temperature (isothermal).
      - Two-phase equilibrium if there's enough mass to form liquid + vapor.
      - If insufficient mass for liquid, treat it as an ideal gas.
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
            initial_fluid_mass: Initial total mass of fluid [kg] (>=0).
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
        self.fluid_mass = initial_fluid_mass
        self.overfill_tolerance = overfill_tolerance
        self.molar_mass = CP.PropsSI("M", fluid_name)  # kg/mol

        self._validate()

    def _validate(self) -> None:
        """
        Validate the tank inputs and physical consistency.

        Raises:
            ValueError: If any field is outside its valid physical range, or if
                the fill is denser than the saturated liquid.
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

        self._check_not_overfilled()

    def _check_not_overfilled(self) -> None:
        """
        Check whether the tank is overfilled within the `overfill_tolerance` threshold.

        Raises:
            ValueError: If the bulk density exceeds the saturated liquid density.
        """
        liquid_density = CP.PropsSI("D", "T", self.temperature, "Q", 0, self.fluid_name)
        bulk_density = self.initial_fluid_mass / self.volume

        if bulk_density > liquid_density * (1 + self.overfill_tolerance):
            raise ValueError(
                f"Tank overfilled: bulk density {bulk_density:.1f} kg/m^3 exceeds "
                f"liquid density {liquid_density:.1f} kg/m^3 for {self.fluid_name} at "
                f"{self.temperature} K"
            )

    def get_pressure(self) -> float:
        """
        Return the tank pressure [Pa].

        1) Compute the saturation pressure at the given temperature.
        2) If the fluid mass is larger than the mass if all vapor at the saturation
            pressure, the tank is partially liquid and the pressure is the saturation
            pressure.
        3) Otherwise, the tank is all vapor and behaves like an ideal gas.

        Returns:
            Tank pressure [Pa].
        """
        saturation_pressure = CP.PropsSI(
            "P", "T", self.temperature, "Q", 0, self.fluid_name
        )
        max_vapor_mass = ideal_gas.get_mass(
            saturation_pressure, self.volume, self.temperature, self.molar_mass
        )

        if self.fluid_mass > max_vapor_mass:
            return saturation_pressure
        else:
            return ideal_gas.get_pressure(
                self.fluid_mass, self.volume, self.temperature, self.molar_mass
            )

    def get_density(self, pressure: float | None = None) -> float:
        """
        Return fluid density [kg/m^3] at tank pressure and temperature.

        1) An empty tank has zero density.
        2) Away from saturation the single-phase density follows directly from
            temperature and pressure.
        3) At saturation that lookup is ambiguous: a partially liquid tank
            returns the saturated liquid density (the feed system pulls liquid
            from the bottom), otherwise it falls back to the bulk density.

        Args:
            pressure: Tank pressure override [Pa], e.g. for a piston-pressurized
                stacked-tank system. Defaults to the tank's own pressure.

        Returns:
            Fluid density [kg/m^3].
        """
        if self.fluid_mass <= 0:
            return 0.0

        tank_pressure = self.get_pressure() if pressure is None else pressure

        try:
            return CP.PropsSI(
                "D", "T", self.temperature, "P", tank_pressure, self.fluid_name
            )
        except ValueError:
            max_vapor_mass = ideal_gas.get_mass(
                tank_pressure, self.volume, self.temperature, self.molar_mass
            )
            if self.fluid_mass > max_vapor_mass:
                return CP.PropsSI("D", "T", self.temperature, "Q", 0, self.fluid_name)
            return self.fluid_mass / self.volume

    def remove_propellant(self, mass: float) -> None:
        """
        Remove the specified mass of fluid [kg] from the tank.

        If the requested mass exceeds what's in the tank, sets total mass to 0.

        Args:
            mass: Mass of fluid to remove [kg].

        Raises:
            ValueError: If `mass` is negative.
        """
        if mass < 0:
            raise ValueError("Cannot remove a negative mass of propellant.")

        self.fluid_mass -= mass
        if self.fluid_mass < 0:
            self.fluid_mass = 0.0
