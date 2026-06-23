import abc
import dataclasses
import math

import machwave.models.thrust_chamber.combustion_chamber as combustion_chamber_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.models.thrust_chamber.nozzle as nozzle_models


def _as_3d_vector(
    name: str, value: tuple[float, float, float]
) -> tuple[float, float, float]:
    """Coerce value to a length-three float tuple, raising if it is not."""
    try:
        components = tuple(float(component) for component in value)
    except TypeError as error:
        raise ValueError(f"{name} must be a length-three sequence") from error
    if len(components) != 3:
        raise ValueError(f"{name} must have three components, got {len(components)}")
    return (components[0], components[1], components[2])


@dataclasses.dataclass(frozen=True, kw_only=True)
class DryMassProperties:
    """
    Overall dry mass properties of a thrust chamber assembly.

    Only required for trajectory (RocketPy) simulations; internal ballistics
    does not use these values.

    Attributes:
        dry_mass: Dry mass of the entire thrust chamber [kg].
        center_of_gravity_coordinate: Dry mass center of gravity position
            measured from the nozzle exit `(x, y, z)` [m]. Positive x points
            toward the bulkhead.
        moment_of_inertia: Dry mass principal moments of inertia
            `(I_11, I_22, I_33)` [kg-m^2], evaluated at the dry mass center of
            gravity. Assumes the thrust chamber is aligned with the x-axis.
    """

    dry_mass: float
    center_of_gravity_coordinate: tuple[float, float, float]
    moment_of_inertia: tuple[float, float, float]

    def __post_init__(self) -> None:
        """
        Validate and normalize the dry mass properties.

        Raises:
            ValueError: If the dry mass is non-positive or non-finite, either
                triple is malformed, or a moment of inertia is negative or
                non-finite.
        """
        if not math.isfinite(self.dry_mass) or self.dry_mass <= 0.0:
            raise ValueError(
                f"dry_mass must be a positive finite number, got {self.dry_mass}"
            )

        cog = _as_3d_vector(
            "center_of_gravity_coordinate", self.center_of_gravity_coordinate
        )
        moment_of_inertia = _as_3d_vector("moment_of_inertia", self.moment_of_inertia)

        if any(not math.isfinite(c) or c < 0.0 for c in moment_of_inertia):
            raise ValueError(
                "moment_of_inertia components must be non-negative finite numbers, got "
                f"{moment_of_inertia}"
            )

        object.__setattr__(self, "center_of_gravity_coordinate", cog)
        object.__setattr__(self, "moment_of_inertia", moment_of_inertia)


class ThrustChamber(abc.ABC):
    """Thrust chamber assembly that ties nozzle, chamber, and injectors together."""

    def __init__(
        self,
        nozzle: nozzle_models.Nozzle,
        combustion_chamber: combustion_chamber_models.CombustionChamber,
        dry_mass_properties: DryMassProperties | None = None,
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

    def require_dry_mass_properties(self) -> DryMassProperties:
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
        dry_mass_properties: DryMassProperties | None = None,
    ):
        """
        Initialize a solid motor thrust chamber.

        Args:
            nozzle: Nozzle instance.
            combustion_chamber: Combustion chamber instance.
            nozzle_exit_to_grain_port_distance: Axial distance from the nozzle
                exit plane to the grain port [m].
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
        dry_mass_properties: DryMassProperties | None = None,
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
