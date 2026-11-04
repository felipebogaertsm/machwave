import typing

import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.adapters.rocketpy.solid_motor as rocketpy_solid_motor

if typing.TYPE_CHECKING:
    import machwave.models.motors as motors_models
    import machwave.simulation.solid.results as solid_results


class RocketPyGenericMotorAdapter(
    rocketpy_base.RocketPyMotorAdapter["solid_results.SolidSimulationResult"]
):
    """
    Adapter to use a simulation result and solid motor as a RocketPy GenericMotor.

    Accepts any grain geometry. The propellant center of mass and inertia come from
    the simulation result, so the chamber dimensions passed to RocketPy only feed its
    descriptive outputs.
    """

    _rocketpy_motor_class = "GenericMotor"

    def __init__(
        self,
        motor: "motors_models.Motor",
        simulation_result: "solid_results.SolidSimulationResult",
    ) -> None:
        """
        Initialize the adapter.

        Args:
            motor: The machwave solid motor.
            simulation_result: The machwave simulation result.
        """
        super().__init__(motor=motor, simulation_result=simulation_result)

        # GenericMotor replaces a dry center of mass at 0.0 with the chamber position
        self.center_of_dry_mass_position = (
            self._get_dry_mass_properties().center_of_gravity_coordinate[0]
        )

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        base_attrs = super()._get_rocketpy_attributes()

        motor = typing.cast("motors_models.SolidMotor", self.motor)

        chamber_radius = motor.thrust_chamber.combustion_chamber.inner_diameter / 2
        chamber_height = motor.grain.total_length
        chamber_position = (
            rocketpy_solid_motor.get_initial_grain_center_of_mass_position(motor)
        )

        return {
            **base_attrs,
            "chamber_radius": chamber_radius,
            "chamber_height": chamber_height,
            "chamber_position": chamber_position,
            "propellant_initial_mass": self.simulation_result.initial_propellant_mass,
        }
