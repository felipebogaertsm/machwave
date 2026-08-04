import abc
import dataclasses

import machwave.common.mass_properties as mass_properties
import machwave.models.thrust_chamber.combustion_chamber as combustion_chamber_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.models.thrust_chamber.nozzle as nozzle_models


@dataclasses.dataclass(kw_only=True)
class ThrustChamber(abc.ABC):
    """
    Base class for a thrust chamber assembly.

    Attributes:
        nozzle: Nozzle instance.
        combustion_chamber: Combustion chamber instance.
        dry_mass_properties: Mass, center of gravity, and inertia of the thrust
            chamber. Optional, not used by the internal ballistics simulation.
    """

    nozzle: nozzle_models.Nozzle
    combustion_chamber: combustion_chamber_models.CombustionChamber
    dry_mass_properties: mass_properties.DryMassProperties | None = None

    def __post_init__(self) -> None:
        """
        Validate that the nozzle fits the combustion chamber.

        Raises:
            ValueError: If the nozzle inlet diameter is larger than the combustion
                chamber casing inner diameter.
        """
        if self.nozzle.inlet_diameter > self.combustion_chamber.casing_inner_diameter:
            raise ValueError(
                f"Nozzle inlet diameter ({self.nozzle.inlet_diameter}) does not fit "
                "within combustion chamber casing_inner_diameter "
                f"({self.combustion_chamber.casing_inner_diameter})"
            )


@dataclasses.dataclass(kw_only=True)
class SolidMotorThrustChamber(ThrustChamber):
    """
    Thrust chamber assembly specialized for solid rocket motors.

    Attributes:
        nozzle: Nozzle instance.
        combustion_chamber: Combustion chamber instance.
        nozzle_exit_to_grain_port_distance: Axial distance from the nozzle exit
            plane to the grain port [m]. Shifts grain mass properties into the motor
            frame, whose origin is the nozzle exit.
        dry_mass_properties: Mass, center of gravity, and inertia of the thrust
            chamber. Optional, not used by the internal ballistics simulation.
    """

    nozzle_exit_to_grain_port_distance: float

    def __post_init__(self) -> None:
        """
        Validate the assembly geometry.

        Raises:
            ValueError: If the nozzle inlet diameter is larger than the combustion
                chamber casing inner diameter, or if the nozzle exit to grain port
                distance is negative.
        """
        super().__post_init__()

        if self.nozzle_exit_to_grain_port_distance < 0.0:
            raise ValueError(
                "nozzle_exit_to_grain_port_distance must be non-negative, got "
                f"{self.nozzle_exit_to_grain_port_distance}"
            )


@dataclasses.dataclass(kw_only=True)
class BiliquidEngineThrustChamber(ThrustChamber):
    """
    Thrust chamber assembly specialized for biliquid rocket engines.

    Attributes:
        nozzle: Nozzle instance.
        injector: Bipropellant injector instance.
        combustion_chamber: Combustion chamber instance.
        dry_mass_properties: Mass, center of gravity, and inertia of the thrust
            chamber. Optional, not used by the internal ballistics simulation.
    """

    injector: injector_models.BipropellantInjector
