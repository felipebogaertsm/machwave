import numpy as np

from machwave.models.propulsion.feed_systems.base import FeedSystem
from machwave.models.propulsion.propellants.biliquid import BiliquidPropellant
from machwave.models.propulsion.thrust_chamber import LiquidEngineThrustChamber
from machwave.services.flow.isentropic import get_ideal_thrust_coefficient

from .base import Motor


class LiquidEngine(Motor[BiliquidPropellant, LiquidEngineThrustChamber]):
    def __init__(
        self,
        propellant: BiliquidPropellant,
        thrust_chamber: LiquidEngineThrustChamber,
        feed_system: FeedSystem,
    ) -> None:
        super().__init__(propellant, thrust_chamber)
        self.feed_system = feed_system

    @property
    def initial_propellant_mass(self) -> float:
        """
        Returns the initial propellant mass in kg.
        """
        return self.feed_system.get_propellant_mass()

    def get_launch_mass(self) -> float:
        return self.thrust_chamber.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        return self.thrust_chamber.dry_mass

    def get_center_of_gravity(self) -> np.typing.NDArray[np.float64]:
        """
        TODO: implement this method.
        """
        return np.array([0, 0, 0])

    def get_thrust_coefficient_correction_factor(self, *args, **kwargs):
        """
        NOTE: temporary implementation, set to 100% efficiency.
        """
        return 1

    def get_thrust_coefficient(
        self,
        chamber_pressure: float,
        exit_pressure: float,
        external_pressure: float,
        expansion_ratio: float,
        k_ex: float,
    ) -> float:
        """
        Args:
            chamber_pressure: Chamber pressure (Pa)
            exit_pressure: Exit pressure (Pa)
            external_pressure: External pressure (Pa)
            expansion_ratio: Expansion ratio
            k_ex: Two-phase isentropic coefficient

        Returns:
            Instantaneous thrust coefficient
        """
        cf_ideal = get_ideal_thrust_coefficient(
            chamber_pressure=chamber_pressure,
            exit_pressure=exit_pressure,
            external_pressure=external_pressure,
            expansion_ratio=expansion_ratio,
            k_ex=k_ex,
        )
        n_cf = self.get_thrust_coefficient_correction_factor()
        return cf_ideal * n_cf
