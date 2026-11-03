import typing

import machwave.adapters.rocketpy.base as rocketpy_base
import machwave.adapters.rocketpy.generic_motor as rocketpy_generic_motor
import machwave.adapters.rocketpy.solid_motor as rocketpy_solid_motor

if typing.TYPE_CHECKING:
    import machwave.models.motors as motors_models
    import machwave.simulation.solid.results as solid_results


def create_rocketpy_motor(
    motor: "motors_models.SolidMotor",
    simulation_result: "solid_results.SolidSimulationResult",
) -> rocketpy_base.RocketPyMotorAdapter["solid_results.SolidSimulationResult"]:
    """
    Adapt a solid motor to the RocketPy motor class that can model its grain.

    Args:
        motor: The machwave solid motor.
        simulation_result: The machwave simulation result.

    Returns:
        A RocketPy SolidMotor for a grain of identical BATES segments, or a RocketPy
        GenericMotor for any other grain.
    """
    if rocketpy_solid_motor.get_solid_motor_incompatibilities(motor.grain):
        return rocketpy_generic_motor.RocketPyGenericMotorAdapter(
            motor=motor, simulation_result=simulation_result
        )
    return rocketpy_solid_motor.RocketPySolidMotorAdapter(
        motor=motor, simulation_result=simulation_result
    )
