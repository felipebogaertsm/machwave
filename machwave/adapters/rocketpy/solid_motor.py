import typing

import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.models.grain.geometries as grain_geometries

if typing.TYPE_CHECKING:
    import machwave.models.grain as grain_models
    import machwave.models.motors as motors_models
    import machwave.simulation.solid.results as solid_results


def get_solid_motor_incompatibilities(grain: "grain_models.Grain") -> list[str]:
    """
    Return the reasons RocketPy's SolidMotor cannot model a grain.

    Args:
        grain: The machwave grain.

    Returns:
        One description per incompatibility, empty if SolidMotor can model the grain.
    """
    if not grain.segments:
        return ["Grain must have at least one segment"]

    incompatibilities: list[str] = []

    mismatches = grain.get_segment_mismatches()
    if mismatches:
        incompatibilities.append(
            "RocketPy SolidMotor requires all grain segments to be "
            "identical, but the following mismatches were found: "
            + "; ".join(mismatches)
        )

    first_segment = grain.segments[0]
    if not isinstance(first_segment, grain_geometries.BatesSegment):
        incompatibilities.append(
            "RocketPy SolidMotor only supports BATES grain geometry, got "
            f"{type(first_segment).__name__}"
        )

    return incompatibilities


def get_initial_grain_center_of_mass_position(
    motor: "motors_models.SolidMotor",
) -> float:
    """
    Return the initial grain center of mass axial position.

    Args:
        motor: The machwave solid motor.

    Returns:
        Axial position measured from the nozzle exit, positive toward the bulkhead [m].
    """
    return (
        motor.grain.get_center_of_gravity(web_distance=0.0)[0]
        + motor.thrust_chamber.nozzle_exit_to_grain_port_distance
    )


class RocketPySolidMotorAdapter(
    rocketpy_base.RocketPyMotorAdapter["solid_results.SolidSimulationResult"]
):
    """Adapter to use a simulation result and motor as a RocketPy SolidMotor."""

    _rocketpy_motor_class = "SolidMotor"

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        base_attrs = super()._get_rocketpy_attributes()

        motor = typing.cast("motors_models.SolidMotor", self.motor)
        grain = motor.grain

        incompatibilities = get_solid_motor_incompatibilities(grain)
        if incompatibilities:
            raise ValueError("; ".join(incompatibilities))

        first_segment = typing.cast(grain_geometries.BatesSegment, grain.segments[0])

        grain_number = grain.segment_count
        grain_separation = grain.spacing
        grain_outer_radius = first_segment.outer_diameter / 2
        grain_initial_height = first_segment.length
        grain_initial_inner_radius = first_segment.core_diameter / 2
        throat_radius = motor.thrust_chamber.nozzle.throat_diameter / 2
        grains_center_of_mass_position = get_initial_grain_center_of_mass_position(
            motor
        )

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

    @property
    def propellant_initial_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        return self.simulation_result.initial_propellant_mass
