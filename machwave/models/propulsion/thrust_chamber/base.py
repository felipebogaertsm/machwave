import abc

import numpy as np

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
        center_of_gravity_coordinate: tuple[float, float, float] | None = None,
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
            center_of_gravity_coordinate:
                3D position (x, y, z) of the dry mass (hardware) center of gravity,
                measured from the nozzle exit, in meters. Positive x values point toward
                the bulkhead. If None, will be estimated from chamber geometry.
        """
        self.nozzle = nozzle
        self.combustion_chamber = combustion_chamber
        self.dry_mass = dry_mass
        self.center_of_gravity_coordinate = (
            np.array(center_of_gravity_coordinate, dtype=np.float64)
            if center_of_gravity_coordinate is not None
            else None
        )


class SolidMotorThrustChamber(ThrustChamber):
    def __init__(
        self,
        nozzle: Nozzle,
        combustion_chamber: CombustionChamber,
        dry_mass: float,
        nozzle_exit_to_grain_port_distance: float,
        center_of_gravity_coordinate: tuple[float, float, float] | None = None,
    ):
        """
        Initialize the SolidMotorThrustChamber.

        Args:
            nozzle:
                An instance of a Nozzle class.
            combustion_chamber:
                An instance of a CombustionChamber class.
            dry_mass:
                The dry mass of the thrust chamber assembly in kg.
            nozzle_exit_to_grain_port_distance:
                Axial distance from nozzle exit plane to the grain port [m].
            center_of_gravity_coordinate:
                3D position (x, y, z) of the dry mass (hardware) center of gravity,
                measured from the nozzle exit, in meters. Positive x values point toward
                the bulkhead. If None, will be estimated from chamber geometry.
        """
        super().__init__(
            nozzle, combustion_chamber, dry_mass, center_of_gravity_coordinate
        )
        self.nozzle_exit_to_grain_port_distance = nozzle_exit_to_grain_port_distance


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
        center_of_gravity_coordinate: tuple[float, float, float] | None = None,
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
            center_of_gravity_coordinate:
                3D position (x, y, z) of the dry mass (hardware) center of gravity,
                measured from the nozzle exit, in meters. Positive x values point toward
                the bulkhead. If None, will be estimated from chamber geometry.
        """
        super().__init__(
            nozzle, combustion_chamber, dry_mass, center_of_gravity_coordinate
        )
        self.injector = injector
