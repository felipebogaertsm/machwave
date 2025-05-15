import numpy as np

from machwave.models.atmosphere import Atmosphere
from machwave.models.rocket import Rocket
from machwave.operations.ballistics._1dof import Ballistic1DOperation
from machwave.simulations.base import Simulation, SimulationParameters


class BallisticSimulationParameters(SimulationParameters):
    """
    Parameters for a ballistic simulation.

    Attributes:
        thrust (np.ndarray): Array of thrust values.
        motor_dry_mass (float): Dry mass of the motor.
        initial_propellant_mass (float): Initial mass of the propellant.
        time (np.ndarray): Array of time values.
        d_t (float): Time step.
        initial_elevation_amsl (float): Initial elevation above mean sea level.
        rail_length (float): Length of the launch rail.
    """

    def __init__(
        self,
        thrust: np.ndarray,
        motor_dry_mass: float,
        initial_propellant_mass: float,
        time: np.ndarray,
        d_t: float,
        initial_elevation_amsl: float,
        rail_length: float,
    ):
        self.thrust = thrust
        self.motor_dry_mass = motor_dry_mass
        self.initial_propellant_mass = initial_propellant_mass
        self.time = time
        self.d_t = d_t
        self.initial_elevation_amsl = initial_elevation_amsl
        self.rail_length = rail_length


class BallisticSimulation(Simulation):
    """
    Ballistic simulation class.

    Attributes:
        rocket (Rocket): The rocket object.
        atmosphere (Atmosphere): The atmosphere object.
        params (BallisticSimulationParameters): The simulation parameters.
        t (np.ndarray): Array of time values.
        ballistic_operation (Ballistic1DOperation): The ballistic operation
            object.
    """

    def __init__(
        self,
        rocket: Rocket,
        atmosphere: Atmosphere,
        params: BallisticSimulationParameters,
    ) -> None:
        """
        Initializes the BallisticSimulation instance.

        Args:
            rocket (Rocket): The rocket object.
            atmosphere (Atmosphere): The atmosphere object.
            params (BallisticSimulationParameters): The simulation parameters.
        """
        super().__init__(params=params)

        self.params: BallisticSimulationParameters = (
            params  # explicitly defining the type of params to avoid pyright error
        )

        self.rocket = rocket
        self.atmosphere = atmosphere
        self.t = np.array([0])
        self.ballistic_operation = None

    def get_propellant_mass(self) -> np.ndarray:
        """
        Computes the propellant mass at each time step.

        Returns:
            np.ndarray: Array of propellant mass values.
        """
        initial_propellant_mass = self.params.initial_propellant_mass
        prop_mass = np.array([])
        time = self.params.time

        for t in time:
            prop_mass = np.append(
                prop_mass, initial_propellant_mass * (time[-1] - t) / time[-1]
            )

        return prop_mass

    def run(self) -> tuple:
        """
        Runs the main loop of the simulation, returning the time array and
        the ballistic operation object.

        Returns:
            tuple[np.array, Ballistic1DOperation]: A tuple containing the time
            array and the ballistic operation object.
        """
        self.ballistic_operation = Ballistic1DOperation(
            self.rocket,
            self.atmosphere,
            rail_length=self.params.rail_length,
            motor_dry_mass=self.rocket.propulsion.get_dry_mass(),
            initial_vehicle_mass=self.rocket.get_launch_mass(),
            initial_elevation_amsl=self.params.initial_elevation_amsl,
        )

        propellant_mass = self.get_propellant_mass()

        i = 0

        while self.ballistic_operation.y[i] >= 0:
            self.t = np.append(self.t, self.t[i] + self.params.d_t)  # new time value

            thrust = np.interp(
                self.t[-1],
                self.params.time,
                self.params.thrust,
                left=0,
                right=0,
            )  # interpolating thrust with new time value

            self.ballistic_operation.run_timestep(
                np.interp(
                    self.t[-1],
                    self.params.time,
                    propellant_mass,
                    left=0,
                    right=0,
                ),  # interpolating propellant mass with new time value
                thrust,
                self.params.d_t,
            )

            i += 1

        return (self.t, self.ballistic_operation)

    def print_results(self):
        """
        Prints the results of the simulation.
        """
        print("\nINTERNAL BALLISTICS COUPLED SIMULATION RESULTS")

        if self.ballistic_operation is not None:
            self.ballistic_operation.print_results()
        else:
            print("Simulation not run yet. Try running the simulation first.")
