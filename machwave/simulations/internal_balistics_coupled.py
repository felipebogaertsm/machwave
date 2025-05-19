"""
The coupled internal ballistics simulation calculates both internal and
external ballistics parameters simulatneously.

The main advantage of this strategy is that, while some environmental
attributes change during flight, they also serve as inputs for the internal
ballistic of the motor. The main attribute that changes during flight is the
ambient pressure, which impacts motor performance.
"""

import numpy as np

from machwave.models.atmosphere import Atmosphere
from machwave.models.rocket import Rocket
from machwave.simulations import Simulation, SimulationParameters
from machwave.simulations.factories import get_motor_state_class
from machwave.states.ballistics._1dof import Ballistic1DState
from machwave.states.internal_ballistics import MotorState


class InternalBallisticsCoupledParams(SimulationParameters):
    """
    Parameters for a coupled internal ballistics simulation.

    Attributes:
        atmosphere (Atmosphere): The atmosphere object.
        d_t (float): Time step for the ballistic simulation.
        dd_t (float): Time step factor for the motor simulation.
        initial_elevation_amsl (float): Initial elevation above mean sea level.
        igniter_pressure (float): Igniter pressure.
        rail_length (float): Length of the launch rail.
    """

    def __init__(
        self,
        atmosphere: Atmosphere,
        d_t: float,
        dd_t: float,
        initial_elevation_amsl: float,
        igniter_pressure: float,
        rail_length: float,
    ) -> None:
        super().__init__()
        self.atmosphere = atmosphere
        self.d_t = d_t
        self.dd_t = dd_t
        self.initial_elevation_amsl = initial_elevation_amsl
        self.igniter_pressure = igniter_pressure
        self.rail_length = rail_length


class InternalBallisticsCoupled(Simulation):
    """
    Coupled internal ballistics simulation class.

    Attributes:
        rocket (Rocket): The rocket object.
        params (InternalBallisticsCoupledParams): The simulation parameters.
        t (np.ndarray): Array of time values.
        motor_state (MotorState): The motor state object.
        ballistic_state (Ballistic1DState): The ballistic state object.
    """

    def __init__(
        self,
        rocket: Rocket,
        params: InternalBallisticsCoupledParams,
    ) -> None:
        """
        Initializes the InternalBallisticsCoupled instance.

        Args:
            rocket (Rocket): The rocket object.
            params (InternalBallisticsCoupledParams): The simulation parameters.
        """
        super().__init__(params=params)

        self.params: InternalBallisticsCoupledParams = (
            params  # explicitly defining the type of params to avoid type errors
        )

        self.rocket = rocket
        self.t = np.array([0])
        self.motor_state = None
        self.ballistic_state = None

    def get_motor_state(self) -> MotorState:
        """
        Returns the motor state object based on the type of the motor.

        Returns:
            MotorState: The motor state object.
        """
        motor_state_class = get_motor_state_class(self.rocket.propulsion)
        return motor_state_class(
            motor=self.rocket.propulsion,
            initial_pressure=self.params.igniter_pressure,
            initial_atmospheric_pressure=self.params.atmosphere.get_pressure(
                self.params.initial_elevation_amsl
            ),
        )

    def run(self) -> tuple:
        """
        Runs the main loop of the simulation, returning the motor state
        and ballistic state objects as a list.

        Returns:
            A list containing the motor state object and the ballistic state object.
        """
        self.motor_state = self.get_motor_state()
        self.ballistic_state = Ballistic1DState(
            self.rocket,
            self.params.atmosphere,
            rail_length=self.params.rail_length,
            motor_dry_mass=self.rocket.propulsion.get_dry_mass(),
            initial_vehicle_mass=self.rocket.get_launch_mass(),
            initial_elevation_amsl=self.params.initial_elevation_amsl,
        )

        i = 0

        while self.ballistic_state.y[i] >= 0 or self.motor_state.m_prop[-1] > 0:
            self.t = np.append(self.t, self.t[i] + self.params.d_t)  # new time value

            if not self.motor_state.end_thrust:
                self.motor_state.run_timestep(
                    self.params.d_t,
                    self.ballistic_state.P_ext[i],
                )
                propellant_mass = self.motor_state.m_prop[i]
                thrust = self.motor_state.thrust[i]
                d_t = self.params.d_t
            else:
                propellant_mass = 0
                thrust = 0
                d_t = self.params.d_t * self.params.dd_t
                self.t[-1] = self.t[-2] + self.params.dd_t * self.params.d_t

            self.ballistic_state.run_timestep(propellant_mass, thrust, d_t)
            i += 1

        return (self.motor_state, self.ballistic_state)

    def print_results(self) -> None:
        print("\nINTERNAL BALLISTICS COUPLED SIMULATION RESULTS")

        if self.motor_state is not None:
            self.motor_state.print_results()
        else:
            print("No motor state results available. Try running the simulation first.")

        if self.ballistic_state is not None:
            self.ballistic_state.print_results()
        else:
            print(
                "No ballistic state results available. Try running the simulation first."
            )
