from machwave.models.propulsion.feed_systems.base import FeedSystem
from machwave.models.propulsion.feed_systems.tanks.base import Tank
from machwave.services.flow.incompressible import mass_flow_orifice


class PressureFedFeedSystem(FeedSystem):
    """
    Concrete implementation of a pressure-fed feed system for a liquid rocket engine.

    This class uses a simplified pressure-difference model with a discharge coefficient
    to calculate the mass flow rates for oxidizer and fuel. The default approach here treats
    the flow as if it passes through a single orifice (the injector).
    """

    def __init__(
        self,
        oxidizer_line_diameter: float,
        oxidizer_line_length: float,
        fuel_line_diameter: float,
        fuel_line_length: float,
        fuel_tank: Tank,
        oxidizer_tank: Tank,
    ):
        """
        Initialize the PressureFedFeedSystem with feedline dimensions, tank objects, and fluid densities.

        Args:
            oxidizer_line_diameter: Diameter of the oxidizer feedline [m].
            oxidizer_line_length: Length of the oxidizer feedline [m].
            fuel_line_diameter: Diameter of the fuel feedline [m].
            fuel_line_length: Length of the fuel feedline [m].
            fuel_tank: An instance representing the fuel tank.
            oxidizer_tank: An instance representing the oxidizer tank.
        """
        super().__init__(fuel_tank, oxidizer_tank)
        self.oxidizer_line_diameter = oxidizer_line_diameter
        self.oxidizer_line_length = oxidizer_line_length
        self.fuel_line_diameter = fuel_line_diameter
        self.fuel_line_length = fuel_line_length

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
        p_up = self.oxidizer_tank.pressure
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

        Args:
            chamber_pressure: Chamber pressure [Pa].
            discharge_coefficient: Discharge coefficient for the injector (dimensionless).
            injector_area: Effective flow area for the fuel injector [m^2].

        Returns:
            Fuel mass flow rate [kg/s].
        """
        p_up = self.fuel_tank.pressure
        p_down = chamber_pressure
        fuel_density = self.fuel_tank.get_density()

        return mass_flow_orifice(
            C_d=discharge_coefficient,
            A=injector_area,
            rho=fuel_density,
            p_up=p_up,
            p_down=p_down,
        )
