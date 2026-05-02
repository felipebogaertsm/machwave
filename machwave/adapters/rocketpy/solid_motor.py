"""RocketPy adapter for Machwave solid motors."""

import typing

from machwave.adapters.rocketpy.base import RocketPyMotorAdapter

if typing.TYPE_CHECKING:
    from machwave.models.motors import SolidMotor
    from machwave.states.solid_motor import (
        SolidMotorState,  # noqa: F401
    )


class RocketPySolidMotorAdapter(RocketPyMotorAdapter["SolidMotorState"]):
    """Adapter to use Machwave SolidMotorState as a RocketPy SolidMotor."""

    _rocketpy_motor_class = "SolidMotor"

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        """Extract motor and grain attributes compatible with RocketPy SolidMotor.

        Returns:
            Attributes for RocketPy SolidMotor initialization.

        Raises:
            ValueError: If grain configuration is incompatible with RocketPy.
        """
        # Get base motor attributes
        base_attrs = super()._get_rocketpy_attributes()

        motor = typing.cast("SolidMotor", self.motor)
        grain = motor.grain

        if not grain.segments:
            raise ValueError("Grain must have at least one segment")

        # RocketPy's SolidMotor assumes all segments are dimensionally identical;
        # silently using segments[0] for a heterogeneous grain (e.g. mixed-length
        # BATES stacks) yields a plausible-but-wrong motor. Fail loud instead.
        mismatches = grain.get_segment_mismatches()
        if mismatches:
            raise ValueError(
                "RocketPy SolidMotor requires all grain segments to be "
                "dimensionally identical, but the following mismatches were "
                "found: " + "; ".join(mismatches)
            )

        first_segment = grain.segments[0]

        grain_number = grain.segment_count
        grain_separation = grain.spacing
        grain_outer_radius = first_segment.outer_diameter / 2
        grain_initial_height = first_segment.length
        throat_radius = motor.thrust_chamber.nozzle.throat_diameter / 2
        grains_center_of_mass_position = motor.grain.get_center_of_gravity(
            web_distance=0.0
        )[0]

        # RocketPy handles real density internally
        grain_density = motor.propellant.ideal_density

        if hasattr(first_segment, "core_diameter"):
            grain_initial_inner_radius = first_segment.core_diameter / 2  # type: ignore[attr-defined]
        else:  # Some geometries might not have core_diameter, use 0 as default
            grain_initial_inner_radius = 0.0

        # Combine base attributes with grain-specific parameters
        solid_motor_attrs = {
            **base_attrs,
            "grain_number": grain_number,
            "grain_density": grain_density,
            "grain_outer_radius": grain_outer_radius,
            "grain_initial_inner_radius": grain_initial_inner_radius,
            "grain_initial_height": grain_initial_height,
            "grain_separation": grain_separation,
            "grains_center_of_mass_position": grains_center_of_mass_position,
            "throat_radius": throat_radius,
        }

        return solid_motor_attrs
