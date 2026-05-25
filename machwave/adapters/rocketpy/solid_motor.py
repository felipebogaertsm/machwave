import typing

import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.models.grain.geometries as grain_geometries

if typing.TYPE_CHECKING:
    import machwave.models.motors as motors_models
    import machwave.simulation.solid.results as solid_results


class RocketPySolidMotorAdapter(
    rocketpy_base.RocketPyMotorAdapter["solid_results.SolidSimulationResult"]
):
    """Adapter to use a simulation result and motor as a RocketPy SolidMotor."""

    _rocketpy_motor_class = "SolidMotor"

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        """Extract motor and grain attributes compatible with RocketPy SolidMotor."""
        base_attrs = super()._get_rocketpy_attributes()

        motor = typing.cast("motors_models.SolidMotor", self.motor)
        grain = motor.grain

        if not grain.segments:
            raise ValueError("Grain must have at least one segment")

        # RocketPy's SolidMotor assumes all segments are identical
        mismatches = grain.get_segment_mismatches()
        if mismatches:
            raise ValueError(
                "RocketPy SolidMotor requires all grain segments to be "
                "identical, but the following mismatches were found: "
                + "; ".join(mismatches)
            )

        first_segment = grain.segments[0]

        # RocketPy's SolidMotor only supports a BATES geometry
        if not isinstance(first_segment, grain_geometries.BatesSegment):
            raise ValueError(
                "RocketPy SolidMotor only supports BATES grain geometry, got "
                f"{type(first_segment).__name__}"
            )

        grain_number = grain.segment_count
        grain_separation = grain.spacing
        grain_outer_radius = first_segment.outer_diameter / 2
        grain_initial_height = first_segment.length
        grain_initial_inner_radius = first_segment.core_diameter / 2
        throat_radius = motor.thrust_chamber.nozzle.throat_diameter / 2
        grains_center_of_mass_position = motor.grain.get_center_of_gravity(
            web_distance=0.0
        )[0]

        # RocketPy handles real density internally
        grain_density = motor.propellant.ideal_density

        # Combine base attributes with grain specific parameters
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
