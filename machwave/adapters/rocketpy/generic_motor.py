import typing

import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.adapters.rocketpy.solid_motor as rocketpy_solid_motor
import machwave.models.motors as motors_models

if typing.TYPE_CHECKING:
    import machwave.models.feed_systems as feed_systems_models
    import machwave.simulation.biliquid.results as biliquid_results
    import machwave.simulation.solid.results as solid_results

GenericMotorSimulationResult: typing.TypeAlias = (
    "solid_results.SolidSimulationResult | biliquid_results.BiliquidSimulationResult"
)


def get_tank_envelope(
    feed_system: "feed_systems_models.FeedSystem",
) -> tuple[float, float, float]:
    """
    Return the cylinder enclosing every tank of the feed system.

    Args:
        feed_system: The machwave feed system.

    Returns:
        The envelope radius [m], its length [m], and the axial position of its center
        measured from the nozzle exit, positive away from the nozzle [m].

    Raises:
        ValueError: If any line has no tank placement.
    """
    radii = []
    aft_ends = []
    forward_ends = []
    for line in feed_system.lines.values():
        tank_placement = line.tank_placement
        if tank_placement is None:
            raise ValueError(
                "RocketPy's 6DOF simulation requires a tank placement on every "
                f"propellant line, got none on {line.name!r}"
            )
        aft_end = tank_placement.nozzle_exit_to_aft_end_distance
        radii.append(tank_placement.inner_diameter / 2)
        aft_ends.append(aft_end)
        forward_ends.append(aft_end + tank_placement.get_length(line.tank.volume))

    envelope_aft_end = min(aft_ends)
    envelope_forward_end = max(forward_ends)
    return (
        max(radii),
        envelope_forward_end - envelope_aft_end,
        (envelope_aft_end + envelope_forward_end) / 2,
    )


class RocketPyGenericMotorAdapter(
    rocketpy_base.RocketPyMotorAdapter[GenericMotorSimulationResult]
):
    """
    Adapter to use a simulation result and motor as a RocketPy GenericMotor.

    Accepts a solid motor of any grain geometry, or a biliquid engine whose tanks are
    all placed. The propellant center of mass and inertia come from the simulation
    result, so the chamber dimensions passed to RocketPy only feed its descriptive
    outputs.
    """

    _rocketpy_motor_class = "GenericMotor"

    def __init__(
        self,
        motor: "motors_models.Motor",
        simulation_result: GenericMotorSimulationResult,
    ) -> None:
        """
        Initialize the adapter.

        Args:
            motor: The machwave solid motor or biliquid engine.
            simulation_result: The machwave simulation result.
        """
        super().__init__(motor=motor, simulation_result=simulation_result)

        # GenericMotor replaces a dry center of mass at 0.0 with the chamber position
        self.center_of_dry_mass_position = (
            self._get_dry_mass_properties().center_of_gravity_coordinate[0]
        )

    def _get_chamber_geometry(self) -> tuple[float, float, float]:
        """
        Return the radius, height, and position of the chamber passed to RocketPy.

        A solid motor's chamber is its grain in the combustion chamber; a biliquid
        engine's is the envelope of its tanks.

        Raises:
            ValueError: If a biliquid engine has a line without a tank placement.
        """
        if isinstance(self.motor, motors_models.BiliquidEngine):
            return get_tank_envelope(self.motor.feed_system)

        motor = typing.cast("motors_models.SolidMotor", self.motor)
        return (
            motor.thrust_chamber.combustion_chamber.inner_diameter / 2,
            motor.grain.total_length,
            rocketpy_solid_motor.get_initial_grain_center_of_mass_position(motor),
        )

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        base_attrs = super()._get_rocketpy_attributes()

        chamber_radius, chamber_height, chamber_position = self._get_chamber_geometry()

        return {
            **base_attrs,
            "chamber_radius": chamber_radius,
            "chamber_height": chamber_height,
            "chamber_position": chamber_position,
            "propellant_initial_mass": self.simulation_result.initial_propellant_mass,
        }
