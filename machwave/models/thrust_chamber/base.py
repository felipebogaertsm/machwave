import abc

import numpy as np

import machwave.models.thrust_chamber.combustion_chamber as combustion_chamber_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.models.thrust_chamber.nozzle as nozzle_models


class ThrustChamber(abc.ABC):
    """Thrust chamber assembly that ties nozzle, chamber, and injectors together."""

    def __init__(
        self,
        nozzle: nozzle_models.Nozzle,
        combustion_chamber: combustion_chamber_models.CombustionChamber,
        dry_mass: float,
        center_of_gravity_coordinate: tuple[float, float, float] | None = None,
    ):
        """
        Initialize a thrust chamber.

        Args:
            nozzle: Nozzle instance.
            combustion_chamber: Combustion chamber instance.
            dry_mass: Dry mass of the thrust chamber assembly [kg].
            center_of_gravity_coordinate: Dry-mass center of gravity position
                `(x, y, z)` [m], measured from the nozzle exit. Positive x
                points toward the bulkhead. If None, estimated from chamber
                geometry.
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
    """Thrust chamber assembly specialized for solid rocket motors."""

    def __init__(
        self,
        nozzle: nozzle_models.Nozzle,
        combustion_chamber: combustion_chamber_models.CombustionChamber,
        dry_mass: float,
        nozzle_exit_to_grain_port_distance: float,
        center_of_gravity_coordinate: tuple[float, float, float] | None = None,
    ):
        """
        Initialize a solid motor thrust chamber.

        Args:
            nozzle: Nozzle instance.
            combustion_chamber: Combustion chamber instance.
            dry_mass: Dry mass of the thrust chamber assembly [kg].
            nozzle_exit_to_grain_port_distance: Axial distance from the nozzle
                exit plane to the grain port [m].
            center_of_gravity_coordinate: Dry-mass center of gravity position
                `(x, y, z)` [m], measured from the nozzle exit. Positive x
                points toward the bulkhead. If None, estimated from chamber
                geometry.
        """
        super().__init__(
            nozzle, combustion_chamber, dry_mass, center_of_gravity_coordinate
        )
        self.nozzle_exit_to_grain_port_distance = nozzle_exit_to_grain_port_distance


class LiquidEngineThrustChamber(ThrustChamber):
    """Thrust chamber assembly specialized for liquid rocket engines."""

    def __init__(
        self,
        nozzle: nozzle_models.Nozzle,
        injector: injector_models.BipropellantInjector,
        combustion_chamber: combustion_chamber_models.CombustionChamber,
        dry_mass: float,
        center_of_gravity_coordinate: tuple[float, float, float] | None = None,
    ):
        """
        Initialize a liquid engine thrust chamber.

        Args:
            nozzle: Nozzle instance.
            injector: Bipropellant injector instance.
            combustion_chamber: Combustion chamber instance.
            dry_mass: Dry mass of the thrust chamber assembly [kg].
            center_of_gravity_coordinate: Dry-mass center of gravity position
                `(x, y, z)` [m], measured from the nozzle exit. Positive x
                points toward the bulkhead. If None, estimated from chamber
                geometry.
        """
        super().__init__(
            nozzle, combustion_chamber, dry_mass, center_of_gravity_coordinate
        )
        self.injector = injector
