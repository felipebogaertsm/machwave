import numpy as np

from machwave.models.propulsion.propellants.liquid import LiquidPropellant
from machwave.models.propulsion.structure import MotorStructure
from machwave.models.propulsion.motors.base import Motor


class LiquidEngine(Motor):
    def __init__(
        self,
        propellant: LiquidPropellant,
        structure: MotorStructure,
    ) -> None:
        super().__init__(propellant, structure)

    def get_launch_mass(self) -> float:
        return self.structure.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        return self.structure.dry_mass

    def get_center_of_gravity(self) -> np.typing.NDArray[np.float64]:
        """
        Constant CG throughout the operation. Half the chamber length.
        """

    def get_thrust_coefficient_correction_factor(self, *args, **kwargs):
        """
        TODO: implement method.
        """

    def get_thrust_coefficient(self, *args, **kwargs):
        """
        TODO: implement method.
        """
