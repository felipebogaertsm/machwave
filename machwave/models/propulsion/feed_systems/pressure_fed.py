from machwave.models.propulsion.feed_systems.tanks import Tank
from machwave.services.flow.incompressible import mass_flow_orifice

from .base import FeedSystem


class StackedTankPressureFedFeedSystem(FeedSystem):
    """
    Represents a bipropellant liquid rocket engine feed system with stacked tanks.

    A stacked tank system is a type of pressure-fed system where the oxidizer and fuel tanks are arranged in a
    vertical stack. The tanks are separated by a piston and the fuel is pressurized by the oxidizer tank.
    """

    def __init__(
        self,
        oxidizer_line_diameter: float,
        oxidizer_line_length: float,
        fuel_line_diameter: float,
        fuel_line_length: float,
        fuel_tank: Tank,
        oxidizer_tank: Tank,
        piston_loss: float = 0.0,
    ):
        """
        Initialize the StackedTankPressureFedFeedSystem with feedline dimensions, tank objects, and fluid densities.

        Args:
            oxidizer_line_diameter: Diameter of the oxidizer feedline [m].
            oxidizer_line_length: Length of the oxidizer feedline [m].
            fuel_line_diameter: Diameter of the fuel feedline [m].
            fuel_line_length: Length of the fuel feedline [m].
            fuel_tank: An instance representing the fuel tank.
            oxidizer_tank: An instance representing the oxidizer tank.
            piston_loss: Pressure loss across the piston [Pa]. Default is 0.0.
        """
        super().__init__(fuel_tank, oxidizer_tank)

        self.oxidizer_line_diameter = oxidizer_line_diameter
        self.oxidizer_line_length = oxidizer_line_length
        self.fuel_line_diameter = fuel_line_diameter
        self.fuel_line_length = fuel_line_length

        self.piston_loss = piston_loss

        # Tank objects
        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

    def get_mass_flow_ox(
        self,
        chamber_pressure: float,
        discharge_coefficient: float,
        injector_area: float,
    ) -> float:
        """
        Compute the current oxidizer mass flow rate via mass_flow_orifice().

        Args:
            chamber_pressure: Chamber pressure [Pa].
            discharge_coefficient: Discharge coefficient for the injector (dimensionless).
            injector_area: Effective flow area for the oxidizer injector [m^2].

        Returns:
            Oxidizer mass flow rate [kg/s].
        """
        p_up = self.get_oxidizer_tank_pressure()
        p_down = chamber_pressure
        oxidizer_density = self.oxidizer_tank.get_density()

        return mass_flow_orifice(
            C_d=discharge_coefficient,
            A=injector_area,
            rho=oxidizer_density,
            p_up=p_up,
            p_down=p_down,
        )

    def get_mass_flow_fuel(
        self,
        chamber_pressure: float,
        discharge_coefficient: float,
        injector_area: float,
    ) -> float:
        """
        Compute the current fuel mass flow rate via mass_flow_orifice().
        The pressure upstream will be the same as the oxidizer tank pressure, since this is a model for a stacked tank.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            discharge_coefficient: Discharge coefficient for the injector (dimensionless).
            injector_area: Effective flow area for the fuel injector [m^2].

        Returns:
            Fuel mass flow rate [kg/s].
        """
        p_up = self.get_oxidizer_tank_pressure() - self.piston_loss
        p_down = chamber_pressure
        fuel_density = self.fuel_tank.get_density()

        return mass_flow_orifice(
            C_d=discharge_coefficient,
            A=injector_area,
            rho=fuel_density,
            p_up=p_up,
            p_down=p_down,
        )

    def get_oxidizer_tank_pressure(self) -> float:
        """
        Returns the tank pressure [Pa].
        """
        return self.oxidizer_tank.get_pressure()

    def get_fuel_tank_pressure(self) -> float:
        """
        Returns the tank pressure [Pa].
        """
        return self.oxidizer_tank.get_pressure()
