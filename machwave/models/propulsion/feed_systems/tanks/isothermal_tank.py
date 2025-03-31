from machwave.models.propulsion.feed_systems.tanks.base import Tank


class IsothermalTank(Tank):
    """A simple isothermal tank model for a liquid rocket engine.

    This model assumes the pressurant gas remains at a constant temperature. The tank
    pressure is computed using the ideal gas law:

        P = (m_gas * R * T) / (volume - (propellant_mass / density))

    Attributes:
        volume: Total internal tank volume [m^3].
        propellant_mass: Current mass of the liquid propellant [kg].
        density: Density of the propellant [kg/m^3].
        mass_gas: Mass of the pressurant gas [kg].
        R: Specific gas constant of the pressurant [J/(kg·K)].
        T: Temperature of the pressurant [K] (assumed constant).
    """

    def __init__(
        self,
        volume: float,
        initial_propellant_mass: float,
        density: float,
        mass_gas: float,
        R: float,
        T: float,
    ):
        """
        Args:
            volume (float): Total internal volume of the tank [m^3].
            initial_propellant_mass (float): Initial mass of the propellant [kg].
            density (float): Density of the liquid propellant [kg/m^3].
            mass_gas (float): Mass of the pressurant gas [kg].
            R (float): Specific gas constant [J/(kg·K)].
            T (float): Temperature [K] (assumed constant for an isothermal model).
        """
        self.volume = volume
        self.propellant_mass = initial_propellant_mass
        self.density = density
        self.mass_gas = mass_gas
        self.R = R
        self.T = T

    def get_pressure(self) -> float:
        """Calculates and returns the current tank pressure [Pa].

        Returns:
            float: The current absolute pressure in the tank [Pa].
        """
        # Volume occupied by the liquid propellant
        liquid_volume = self.propellant_mass / self.density

        # Compute the free gas volume
        gas_volume = self.volume - liquid_volume
        if gas_volume <= 0.0:
            raise ValueError("Tank is completely filled with liquid propellant.")

        # Tank pressure using the ideal gas law
        return (self.mass_gas * self.R * self.T) / gas_volume

    def remove_propellant(self, mass: float) -> None:
        """Removes a specified mass of propellant from the tank.

        Args:
            mass (float): The mass of propellant to remove [kg].
        """
        self.propellant_mass = max(self.propellant_mass - mass, 0.0)
