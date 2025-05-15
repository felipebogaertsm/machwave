import abc

from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
    CombustionChamber,
)
from machwave.models.propulsion.thrust_chamber.injector import BipropellantInjector
from machwave.models.propulsion.thrust_chamber.nozzle import Nozzle


class ThrustChamber(abc.ABC):
    """
    Represents the thrust chamber assembly of a liquid rocket engine.
    ThrustChamber acts as a coordinating layer that ties these elements together.
    """

    def __init__(
        self,
        nozzle: Nozzle,
        combustion_chamber: CombustionChamber,
        dry_mass: float,
    ):
        """
        Initialize the ThrustChamber.

        Args:
            nozzle:
                An instance of a Nozzle class.
            combustion_chamber:
                An instance of a CombustionChamber class.
            dry_mass:
                The dry mass of the thrust chamber assembly in kg.
        """
        self.nozzle = nozzle
        self.combustion_chamber = combustion_chamber
        self.dry_mass = dry_mass


class SolidMotorThrustChamber(ThrustChamber):
    def __init__(
        self,
        nozzle: Nozzle,
        combustion_chamber: CombustionChamber,
        dry_mass: float,
    ):
        super().__init__(nozzle, combustion_chamber, dry_mass)


class LiquidEngineThrustChamber(ThrustChamber):
    """
    Represents the thrust chamber assembly of a liquid rocket engine.
    This class is a specialization of the ThrustChamber class for liquid rocket engines.
    """

    def __init__(
        self,
        nozzle: Nozzle,
        injector: BipropellantInjector,
        combustion_chamber: CombustionChamber,
        dry_mass: float,
    ):
        """
        Initialize the LiquidEngineThrustChamber.

        Args:
            nozzle:
                An instance of a Nozzle class.
            injector:
                An instance of an Injector class.
            combustion_chamber:
                An instance of a CombustionChamber class.
            dry_mass:
                The dry mass of the thrust chamber assembly in kg.
        """
        super().__init__(nozzle, combustion_chamber, dry_mass)
        self.injector = injector
