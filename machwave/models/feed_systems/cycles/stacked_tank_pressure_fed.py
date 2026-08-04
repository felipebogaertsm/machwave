import machwave.models.feed_systems.base as feed_system_base
import machwave.models.feed_systems.tank as tank


class StackedTankPressureFedFeedSystem(feed_system_base.FeedSystem):
    """
    Represents a bipropellant biliquid rocket engine feed system with stacked tanks.

    A stacked tank system is a type of pressure-fed system where the oxidizer and fuel
    tanks are arranged in a vertical stack. The tanks are separated by a piston and the
    fuel is pressurized by the oxidizer tank.
    """

    def __init__(
        self,
        fuel_tank: tank.Tank,
        oxidizer_tank: tank.Tank,
        piston_loss: float = 0.0,
        oxidizer_line_loss: float = 0.0,
        fuel_line_loss: float = 0.0,
    ):
        """
        Initialize the StackedTankPressureFedFeedSystem.

        Args:
            fuel_tank: An instance representing the fuel tank.
            oxidizer_tank: An instance representing the oxidizer tank.
            piston_loss: Pressure loss across the piston [Pa]. Default is 0.0.
            oxidizer_line_loss: Pressure loss along the oxidizer feedline [Pa],
                stated for the design flow rather than computed from it.
                Default is 0.0, no line.
            fuel_line_loss: Pressure loss along the fuel feedline [Pa], stated
                for the design flow rather than computed from it. Default is
                0.0, no line.

        Raises:
            ValueError: If any pressure loss is negative.
        """
        super().__init__(fuel_tank, oxidizer_tank)

        self.piston_loss = piston_loss
        self.oxidizer_line_loss = oxidizer_line_loss
        self.fuel_line_loss = fuel_line_loss

        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

        self._validate()

    def _validate(self) -> None:
        """
        Validate the pressure losses.

        Raises:
            ValueError: If any pressure loss is negative.
        """
        for name, value in (
            ("piston_loss", self.piston_loss),
            ("oxidizer_line_loss", self.oxidizer_line_loss),
            ("fuel_line_loss", self.fuel_line_loss),
        ):
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value}")

    def get_oxidizer_tank_pressure(
        self, *, oxidizer_mass: float, oxidizer_internal_energy: float | None = None
    ) -> float:
        """
        Returns the oxidizer-side pressure delivered to the injector [Pa].

        The tank pressure less what the oxidizer line takes.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.
        """
        return (
            self.oxidizer_tank.get_pressure(oxidizer_mass, oxidizer_internal_energy)
            - self.oxidizer_line_loss
        )

    def get_fuel_tank_pressure(
        self,
        *,
        oxidizer_mass: float,
        fuel_mass: float,
        fuel_internal_energy: float | None = None,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Returns the fuel-side pressure delivered to the injector [Pa].

        In a stacked-tank system the fuel is pressurized by the oxidizer
        through the piston, so the fuel side starts from the oxidizer tank
        pressure less the piston pressure loss, and then loses what the fuel
        line takes. The oxidizer line is not on this path, and neither
        ``fuel_mass`` nor ``fuel_internal_energy`` is used here.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            fuel_mass: Current fuel mass in the tank [kg].
            fuel_internal_energy: Current internal energy of the fuel [J].
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J], which sets the pressure the piston passes on. Required for
                a tank running an energy balance, unused otherwise.
        """
        return (
            self.oxidizer_tank.get_pressure(oxidizer_mass, oxidizer_internal_energy)
            - self.piston_loss
            - self.fuel_line_loss
        )
