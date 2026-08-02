import abc

import machwave.common.mass_properties as mass_properties
import machwave.models.thrust_chamber.combustion_chamber as combustion_chamber_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.models.thrust_chamber.nozzle as nozzle_models


class ThrustChamber(abc.ABC):
    """Thrust chamber assembly that ties nozzle, chamber, and injectors together."""

    def __init__(
        self,
        nozzle: nozzle_models.Nozzle,
        combustion_chamber: combustion_chamber_models.CombustionChamber,
        dry_mass_properties: mass_properties.DryMassProperties | None = None,
    ):
        """
        Initialize a thrust chamber.

        Args:
            nozzle: Nozzle instance.
            combustion_chamber: Combustion chamber instance.
            dry_mass_properties: Dry mass properties of the assembly. Optional;
                only consumed by the RocketPy trajectory adapter. Internal
                ballistics simulations do not require it.
        """
        self.nozzle = nozzle
        self.combustion_chamber = combustion_chamber
        self.dry_mass_properties = dry_mass_properties

        self._validate()

    def _validate(self) -> None:
        """
        Validate that the components fit together.

        Raises:
            ValueError: If the nozzle inlet does not fit within the combustion
                chamber bore.
        """
        if self.nozzle.inlet_diameter > self.combustion_chamber.casing_inner_diameter:
            raise ValueError(
                f"nozzle inlet_diameter ({self.nozzle.inlet_diameter}) does not fit "
                "within combustion chamber casing_inner_diameter "
                f"({self.combustion_chamber.casing_inner_diameter})"
            )

    def require_dry_mass_properties(self) -> mass_properties.DryMassProperties:
        """
        Return the dry mass properties, raising if they are not defined.

        Raises:
            ValueError: If the dry mass properties were not provided.
        """
        if self.dry_mass_properties is None:
            raise ValueError(
                "Dry mass properties are not defined for this thrust chamber"
            )
        return self.dry_mass_properties


class SolidMotorThrustChamber(ThrustChamber):
    """Thrust chamber assembly specialized for solid rocket motors."""

    def __init__(
        self,
        nozzle: nozzle_models.Nozzle,
        combustion_chamber: combustion_chamber_models.CombustionChamber,
        nozzle_exit_to_grain_port_distance: float,
        dry_mass_properties: mass_properties.DryMassProperties | None = None,
    ):
        """
        Initialize a solid motor thrust chamber.

        Args:
            nozzle: Nozzle instance.
            combustion_chamber: Combustion chamber instance.
            nozzle_exit_to_grain_port_distance: Axial distance from the nozzle
                exit plane to the grain port [m]. Shifts grain mass properties
                into the motor frame, whose origin is the nozzle exit.
            dry_mass_properties: Dry mass properties of the assembly. Optional;
                only consumed by the RocketPy trajectory adapter. Internal
                ballistics simulations do not require it.
        """
        super().__init__(nozzle, combustion_chamber, dry_mass_properties)
        self.nozzle_exit_to_grain_port_distance = nozzle_exit_to_grain_port_distance

        if nozzle_exit_to_grain_port_distance < 0.0:
            raise ValueError(
                "nozzle_exit_to_grain_port_distance must be non-negative, got "
                f"{nozzle_exit_to_grain_port_distance}"
            )


class BiliquidEngineThrustChamber(ThrustChamber):
    """Thrust chamber assembly specialized for biliquid rocket engines."""

    def __init__(
        self,
        nozzle: nozzle_models.Nozzle,
        injector: injector_models.BipropellantInjector,
        combustion_chamber: combustion_chamber_models.CombustionChamber,
        dry_mass_properties: mass_properties.DryMassProperties | None = None,
    ):
        """
        Initialize a biliquid engine thrust chamber.

        Args:
            nozzle: Nozzle instance.
            injector: Bipropellant injector instance.
            combustion_chamber: Combustion chamber instance.
            dry_mass_properties: Dry mass properties of the assembly. Optional;
                only consumed by the RocketPy trajectory adapter. Internal
                ballistics simulations do not require it.
        """
        super().__init__(nozzle, combustion_chamber, dry_mass_properties)
        self.injector = injector
