from .chamber import CombustionChamber
from .nozzle import Nozzle


class MotorStructure:
    def __init__(
        self,
        safety_factor,
        dry_mass,
        nozzle: Nozzle,
        chamber: CombustionChamber,
    ):
        self.safety_factor = safety_factor
        self.dry_mass = dry_mass
        self.nozzle = nozzle
        self.chamber = chamber
