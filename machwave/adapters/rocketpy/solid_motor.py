"""RocketPy adapter for Machwave solid motors."""

import typing

from machwave.adapters.rocketpy.base import RocketPyMotorAdapter

if typing.TYPE_CHECKING:
    from machwave.states.internal_ballistics.solid_motor import SolidMotorState


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

        motor = self.motor
        grain = motor.grain

        if not grain.segments:
            raise ValueError("Grain must have at least one segment")

        # RocketPy's SolidMotor assumes all segments are identical, use first one
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
            grain_initial_inner_radius = first_segment.core_diameter / 2
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
