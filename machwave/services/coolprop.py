"""Fluid property service wrapper around CoolProp."""

import typing

import scipy.optimize

import machwave.common.extras as extras

try:
    import CoolProp.CoolProp as CP
except ImportError as e:  # pragma: no cover - exercised only without coolprop
    raise extras.MissingOptionalDependencyError("CoolProp", extras.LIQUID) from e

# a converged flash is off by under 1e-8 J/kg, a wrong one by tens of kJ/kg
INTERNAL_ENERGY_TOLERANCE = 1.0  # [J/kg]
# the saturation curve is undefined at the critical point itself
CRITICAL_TEMPERATURE_BRACKET_MARGIN = 1e-8
DOME_TEMPERATURE_TOLERANCE = 1e-10  # [K]


class CoolPropService:
    """Thin wrapper around CoolProp `PropsSI` bound to a single fluid."""

    def __init__(self, fluid_name: str) -> None:
        """
        Initialize the service.

        Args:
            fluid_name: Name of the fluid in the CoolProp database.
        """
        self.fluid_name = fluid_name

    def get_triple_point_temperature(self) -> float:
        """
        Get the triple point temperature of the fluid.

        Returns:
            Triple point temperature [K].
        """
        return CP.PropsSI("Ttriple", self.fluid_name)

    def get_critical_temperature(self) -> float:
        """
        Get the critical temperature of the fluid.

        Returns:
            Critical temperature [K].
        """
        return CP.PropsSI("Tcrit", self.fluid_name)

    def get_saturation_pressure(self, temperature: float) -> float:
        """
        Get the saturation pressure on the liquid side of the saturation curve.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturation pressure [Pa].
        """
        return CP.PropsSI("P", "T", temperature, "Q", 0, self.fluid_name)

    def get_saturated_liquid_density(self, temperature: float) -> float:
        """
        Get the saturated-liquid density at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-liquid density [kg/m^3].
        """
        return CP.PropsSI("D", "T", temperature, "Q", 0, self.fluid_name)

    def get_saturated_vapor_density(self, temperature: float) -> float:
        """
        Get the saturated-vapor density at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-vapor density [kg/m^3].
        """
        return CP.PropsSI("D", "T", temperature, "Q", 1, self.fluid_name)

    def get_saturated_liquid_enthalpy(self, temperature: float) -> float:
        """
        Get the saturated-liquid specific enthalpy at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-liquid specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "Q", 0, self.fluid_name)

    def get_saturated_vapor_enthalpy(self, temperature: float) -> float:
        """
        Get the saturated-vapor specific enthalpy at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-vapor specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "Q", 1, self.fluid_name)

    def get_saturated_liquid_entropy(self, temperature: float) -> float:
        """
        Get the saturated-liquid specific entropy at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-liquid specific entropy [J/(kg K)].
        """
        return CP.PropsSI("S", "T", temperature, "Q", 0, self.fluid_name)

    def get_pressure_at_temperature_density(
        self, temperature: float, density: float
    ) -> float:
        """
        Get the single-phase pressure at a given temperature and density.

        Args:
            temperature: Temperature [K].
            density: Density [kg/m^3].

        Returns:
            Pressure [Pa].
        """
        return CP.PropsSI("P", "T", temperature, "D", density, self.fluid_name)

    def get_internal_energy_at_temperature_density(
        self, temperature: float, density: float
    ) -> float:
        """
        Get the specific internal energy at a given temperature and density.

        Args:
            temperature: Temperature [K].
            density: Density [kg/m^3].

        Returns:
            Specific internal energy [J/kg].
        """
        return CP.PropsSI("U", "T", temperature, "D", density, self.fluid_name)

    def get_temperature_at_density_internal_energy(
        self, density: float, internal_energy: float
    ) -> float:
        """
        Get the temperature at a given density and specific internal energy.

        The CoolProp flash is checked against the saturation curve.

        Args:
            density: Density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            Temperature [K].

        Raises:
            ValueError: If the state is supercritical, or if it is neither a
                converged single-phase state nor on the saturation dome.
        """
        return self._get_temperature_pressure_at_density_internal_energy(
            density, internal_energy
        )[0]

    def get_pressure_at_density_internal_energy(
        self, density: float, internal_energy: float
    ) -> float:
        """
        Get the pressure at a given density and specific internal energy.

        The CoolProp flash is checked against the saturation curve.

        Args:
            density: Density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            Pressure [Pa].

        Raises:
            ValueError: If the state is supercritical, or if it is neither a
                converged single-phase state nor on the saturation dome.
        """
        return self._get_temperature_pressure_at_density_internal_energy(
            density, internal_energy
        )[1]

    def _get_temperature_pressure_at_density_internal_energy(
        self, density: float, internal_energy: float
    ) -> tuple[float, float]:
        """
        Get the temperature and pressure at a density and internal energy.

        CoolProp 6.8 can silently return a single-phase state for a point inside the
        saturation dome. The flash is kept only if its temperature gives back the
        internal energy. Otherwise the state is solved on the dome.

        Args:
            density: Density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            Temperature [K] and pressure [Pa].

        Raises:
            ValueError: If the state is supercritical, or if it is neither a
                converged single-phase state nor on the saturation dome.
        """
        try:
            temperature = CP.PropsSI(
                "T", "D", density, "U", internal_energy, self.fluid_name
            )
            pressure = CP.PropsSI(
                "P", "D", density, "U", internal_energy, self.fluid_name
            )
        except ValueError:
            return self._solve_on_the_dome(density, internal_energy)

        critical_temperature = self.get_critical_temperature()
        if temperature >= critical_temperature:
            raise ValueError(
                f"{self.fluid_name} at {density} kg/m^3 and {internal_energy} J/kg "
                f"is supercritical at {temperature} K; the saturation model holds "
                f"only below the critical temperature {critical_temperature} K"
            )

        saturated_liquid_density = self.get_saturated_liquid_density(temperature)
        saturated_vapor_density = self.get_saturated_vapor_density(temperature)
        if saturated_vapor_density < density < saturated_liquid_density:
            residual, _ = self._get_dome_residual(temperature, density, internal_energy)
            is_consistent = abs(residual) <= INTERNAL_ENERGY_TOLERANCE
        else:
            is_consistent = (
                abs(
                    self.get_internal_energy_at_temperature_density(
                        temperature, density
                    )
                    - internal_energy
                )
                <= INTERNAL_ENERGY_TOLERANCE
            )

        if is_consistent:
            return temperature, pressure
        return self._solve_on_the_dome(density, internal_energy)

    def _get_dome_residual(
        self, temperature: float, density: float, internal_energy: float
    ) -> tuple[float, float]:
        """
        Get the internal energy residual of a two-phase mix at the density.

        Args:
            temperature: Saturation temperature [K].
            density: Bulk density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            The residual [J/kg] and the quality [-].
        """
        liquid_volume = 1.0 / self.get_saturated_liquid_density(temperature)
        vapor_volume = 1.0 / self.get_saturated_vapor_density(temperature)
        liquid_energy = CP.PropsSI("U", "T", temperature, "Q", 0, self.fluid_name)
        vapor_energy = CP.PropsSI("U", "T", temperature, "Q", 1, self.fluid_name)
        quality = (1.0 / density - liquid_volume) / (vapor_volume - liquid_volume)
        residual = (
            liquid_energy + quality * (vapor_energy - liquid_energy) - internal_energy
        )
        return residual, quality

    def _solve_on_the_dome(
        self, density: float, internal_energy: float
    ) -> tuple[float, float]:
        """
        Solve for the two-phase temperature at a density and internal energy.

        At constant density the mix internal energy rises with temperature. The root
        is bracketed between the triple point and just under the critical point.

        Args:
            density: Bulk density [kg/m^3].
            internal_energy: Specific internal energy [J/kg].

        Returns:
            Temperature [K] and saturation pressure [Pa].

        Raises:
            ValueError: If no two-phase state at that density holds that
                internal energy.
        """

        def get_residual(temperature: float) -> float:
            return self._get_dome_residual(temperature, density, internal_energy)[0]

        not_on_the_dome = ValueError(
            f"{self.fluid_name} at {density} kg/m^3 and {internal_energy} J/kg is "
            "neither a converged single-phase state nor on the saturation dome"
        )
        lower_temperature = self.get_triple_point_temperature()
        upper_temperature = self.get_critical_temperature() * (
            1.0 - CRITICAL_TEMPERATURE_BRACKET_MARGIN
        )
        if get_residual(lower_temperature) * get_residual(upper_temperature) > 0.0:
            raise not_on_the_dome

        temperature = typing.cast(
            float,
            scipy.optimize.brentq(
                get_residual,
                lower_temperature,
                upper_temperature,
                xtol=DOME_TEMPERATURE_TOLERANCE,
            ),
        )
        _, quality = self._get_dome_residual(temperature, density, internal_energy)
        if not 0.0 <= quality <= 1.0:
            raise not_on_the_dome

        return temperature, self.get_saturation_pressure(temperature)

    def get_enthalpy_at_temperature_density(
        self, temperature: float, density: float
    ) -> float:
        """
        Get the specific enthalpy at a given temperature and density.

        Args:
            temperature: Temperature [K].
            density: Density [kg/m^3].

        Returns:
            Specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "D", density, self.fluid_name)

    def get_enthalpy_at_temperature_pressure(
        self, temperature: float, pressure: float
    ) -> float:
        """
        Get the specific enthalpy at a given temperature and pressure.

        Args:
            temperature: Temperature [K].
            pressure: Pressure [Pa].

        Returns:
            Specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "T", temperature, "P", pressure, self.fluid_name)

    def get_entropy_at_temperature_pressure(
        self, temperature: float, pressure: float
    ) -> float:
        """
        Get the specific entropy at a given temperature and pressure.

        Args:
            temperature: Temperature [K].
            pressure: Pressure [Pa].

        Returns:
            Specific entropy [J/(kg K)].
        """
        return CP.PropsSI("S", "T", temperature, "P", pressure, self.fluid_name)

    def get_density_at_pressure_entropy(self, pressure: float, entropy: float) -> float:
        """
        Get the density at a given pressure and specific entropy.

        Args:
            pressure: Pressure [Pa].
            entropy: Specific entropy [J/(kg K)].

        Returns:
            Density [kg/m^3].
        """
        return CP.PropsSI("D", "P", pressure, "S", entropy, self.fluid_name)

    def get_enthalpy_at_pressure_entropy(
        self, pressure: float, entropy: float
    ) -> float:
        """
        Get the specific enthalpy at a given pressure and specific entropy.

        Args:
            pressure: Pressure [Pa].
            entropy: Specific entropy [J/(kg K)].

        Returns:
            Specific enthalpy [J/kg].
        """
        return CP.PropsSI("H", "P", pressure, "S", entropy, self.fluid_name)
