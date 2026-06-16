"""Fluid property service wrapper around CoolProp."""

import CoolProp.CoolProp as CP


class CoolPropService:
    """Thin wrapper around CoolProp `PropsSI` bound to a single fluid."""

    def __init__(self, fluid_name: str) -> None:
        """
        Initialize the service.

        Args:
            fluid_name: Name of the fluid in the CoolProp database.
        """
        self.fluid_name = fluid_name

    def get_molar_mass(self) -> float:
        """
        Get the molar mass of the fluid.

        Returns:
            Molar mass [kg/mol].
        """
        return CP.PropsSI("M", self.fluid_name)

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

    def get_saturated_liquid_entropy(self, temperature: float) -> float:
        """
        Get the saturated-liquid specific entropy at a given temperature.

        Args:
            temperature: Temperature [K].

        Returns:
            Saturated-liquid specific entropy [J/(kg K)].
        """
        return CP.PropsSI("S", "T", temperature, "Q", 0, self.fluid_name)

    def get_density_at_temperature_pressure(
        self, temperature: float, pressure: float
    ) -> float:
        """
        Get the single-phase density at a given temperature and pressure.

        Args:
            temperature: Temperature [K].
            pressure: Pressure [Pa].

        Returns:
            Density [kg/m^3].
        """
        return CP.PropsSI("D", "T", temperature, "P", pressure, self.fluid_name)

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
