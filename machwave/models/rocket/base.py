from machwave.models.propulsion.motors import Motor
from machwave.models.recovery import Recovery
from machwave.models.rocket.fuselage import Fuselage


class Rocket:
    """
    A Rocket with propulsion, recovery system, fuselage and
    a specified dry-structure mass (mass_without_motor).
    """

    def __init__(
        self,
        propulsion: Motor,
        recovery: Recovery,
        fuselage: Fuselage,
        mass_without_motor: float,
    ) -> None:
        """
        Args:
            propulsion (Motor): the rocket motor or propulsion system.
            recovery (Recovery): the recovery system (parachute, etc.).
            fuselage (Fuselage): the rocket body.
            mass_without_motor (float): structure + avionics + recovery + fuselage mass [kg].
        """
        self.propulsion = propulsion
        self.recovery = recovery
        self.fuselage = fuselage
        self.mass_without_motor = mass_without_motor

    def get_launch_mass(self) -> float:
        """
        Total mass at liftoff = dry-structure + propellant.
        """
        return self.mass_without_motor + self.propulsion.get_launch_mass()

    def get_dry_mass(self) -> float:
        """
        Total dry mass = structure + inert mass of the motor.
        """
        return self.mass_without_motor + self.propulsion.get_dry_mass()
