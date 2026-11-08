import typing

import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.adapters.rocketpy.generic_motor as rocketpy_generic_motor
import machwave.adapters.rocketpy.solid_motor as rocketpy_solid_motor
import machwave.models.motors as motors_models

if typing.TYPE_CHECKING:
    import machwave.simulation.solid.results as solid_results


def create_rocketpy_motor(
    motor: motors_models.Motor,
    simulation_result: rocketpy_generic_motor.GenericMotorSimulationResult,
) -> rocketpy_base.RocketPyMotorAdapter[typing.Any]:
    """
    Adapt a motor to the RocketPy motor class that can model it.

    Args:
        motor: The machwave solid motor or biliquid engine.
        simulation_result: The machwave simulation result.

    Returns:
        A RocketPy SolidMotor for a grain of identical BATES segments, or a RocketPy
        GenericMotor for any other grain and for a biliquid engine.

    Raises:
        ValueError: If a solid motor's grain has no segments.
    """
    if isinstance(
        motor, motors_models.SolidMotor
    ) and rocketpy_solid_motor.is_supported_by_solid_motor(motor.grain):
        return rocketpy_solid_motor.RocketPySolidMotorAdapter(
            motor=motor,
            simulation_result=typing.cast(
                "solid_results.SolidSimulationResult", simulation_result
            ),
        )
    return rocketpy_generic_motor.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=simulation_result
    )
