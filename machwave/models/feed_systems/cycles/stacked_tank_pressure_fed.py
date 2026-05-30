import machwave.models.feed_systems.base as feed_system_base
import machwave.models.feed_systems.tank as tank
import machwave.models.thrust_chamber.injector as injector_models


class StackedTankPressureFedFeedSystem(feed_system_base.FeedSystem):
    """
    Represents a bipropellant biliquid rocket engine feed system with stacked tanks.

    A stacked tank system is a type of pressure-fed system where the oxidizer and fuel
    tanks are arranged in a vertical stack. The tanks are separated by a piston and the
    fuel is pressurized by the oxidizer tank.
    """

    def __init__(
        self,
        oxidizer_line_diameter: float,
        oxidizer_line_length: float,
        fuel_line_diameter: float,
        fuel_line_length: float,
        fuel_tank: tank.Tank,
        oxidizer_tank: tank.Tank,
        piston_loss: float = 0.0,
    ):
        """
        Initialize the StackedTankPressureFedFeedSystem.

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

        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

    def get_mass_flow_ox(
        self,
        chamber_pressure: float,
        *,
        injector: injector_models.BipropellantInjector,
        oxidizer_mass: float,
    ) -> float:
        """
        Compute the current oxidizer mass flow rate by delegating to the injector.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            oxidizer_mass: Current oxidizer mass in the tank [kg].

        Returns:
            Oxidizer mass flow rate [kg/s].
        """
        return injector.get_mass_flow_ox(
            tank=self.oxidizer_tank,
            pressure_upstream=self.get_oxidizer_tank_pressure(
                oxidizer_mass=oxidizer_mass
            ),
            chamber_pressure=chamber_pressure,
            fluid_mass=oxidizer_mass,
        )

    def get_mass_flow_fuel(
        self,
        chamber_pressure: float,
        *,
        injector: injector_models.BipropellantInjector,
        fuel_mass: float,
        oxidizer_mass: float,
    ) -> float:
        """
        Compute the current fuel mass flow rate by delegating to the injector.

        The upstream pressure is the oxidizer tank pressure minus the piston
        loss, since this models a stacked tank pressurized through the piston.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            fuel_mass: Current fuel mass in the tank [kg].
            oxidizer_mass: Current oxidizer mass in the tank [kg].

        Returns:
            Fuel mass flow rate [kg/s].
        """
        return injector.get_mass_flow_fuel(
            tank=self.fuel_tank,
            pressure_upstream=self.get_fuel_tank_pressure(
                oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass
            ),
            chamber_pressure=chamber_pressure,
            fluid_mass=fuel_mass,
        )

    def get_oxidizer_tank_pressure(self, *, oxidizer_mass: float) -> float:
        """Returns the tank pressure [Pa]."""
        return self.oxidizer_tank.get_pressure(oxidizer_mass)

    def get_fuel_tank_pressure(
        self, *, oxidizer_mass: float, fuel_mass: float
    ) -> float:
        """
        Returns the fuel-side upstream pressure [Pa].

        In a stacked-tank system the fuel is pressurized by the oxidizer
        through the piston, so the fuel-side pressure is the oxidizer tank
        pressure minus the piston pressure loss; ``fuel_mass`` is unused here.
        """
        return (
            self.get_oxidizer_tank_pressure(oxidizer_mass=oxidizer_mass)
            - self.piston_loss
        )
