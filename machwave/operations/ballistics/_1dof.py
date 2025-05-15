import numpy as np

from machwave.models.atmosphere import Atmosphere
from machwave.models.rocket import Rocket
from machwave.operations.ballistics.base import BallisticOperation
from machwave.services.equations import ballistics_ode
from machwave.solvers.odes import rk4th_ode_solver


class Ballistic1DOperation(BallisticOperation):
    """Stores and processes a ballistics operation (aka flight)."""

    def __init__(
        self,
        rocket: Rocket,
        atmosphere: Atmosphere,
        rail_length: float,
        motor_dry_mass: float,
        initial_vehicle_mass: float,
        initial_elevation_amsl: float = 0,
    ) -> None:
        """
        Initialize the attributes for the ballistics operation.

        Args:
            rocket (Rocket): The rocket used for the operation.
            atmosphere (Atmosphere): The atmospheric conditions.
            rail_length (float): The length of the rail for launch.
            motor_dry_mass (float): The dry mass of the motor.
            initial_vehicle_mass (float): The initial mass of the vehicle.
            initial_elevation_amsl (float, optional): The initial elevation above mean sea level (AMSL). Defaults to 0.
        """
        self.rocket = rocket
        self.atmosphere = atmosphere
        self.rail_length = rail_length
        self.motor_dry_mass = motor_dry_mass
        self.initial_elevation_amsl = initial_elevation_amsl

        self.t = np.array([0])  # time vector

        self.P_ext = np.array(
            [self.atmosphere.get_pressure(initial_elevation_amsl)]
        )  # external pressure
        self.rho_air = np.array(
            [self.atmosphere.get_density(initial_elevation_amsl)]
        )  # air density
        self.g = np.array(
            [self.atmosphere.get_gravity(initial_elevation_amsl)]
        )  # acceleration of gravity
        self.vehicle_mass = np.array(
            [initial_vehicle_mass]
        )  # total mass of the vehicle

        # Spacial params:
        self.y = np.array([0])  # altitude, AGL
        self.v = np.array([0])  # velocity
        self.acceleration = np.array([0])  # acceleration
        self.mach_no = np.array([0])  # Mach number

        self.velocity_out_of_rail = None

    @property
    def apogee(self) -> float:
        """Get the apogee of the operation."""
        return np.max(self.y)

    @property
    def apogee_time(self) -> float:
        """Get the time of the apogee."""
        return self.t[np.argmax(self.y)]

    @property
    def max_velocity(self) -> float:
        """Get the maximum velocity of the operation."""
        return np.max(self.v)

    @property
    def max_velocity_time(self) -> float:
        """Get the time of the maximum velocity."""
        return self.t[np.argmax(self.v)]

    def run_timestep(self, propellant_mass: float, thrust: float, d_t: float) -> None:
        """
        Perform an iteration of the ballistics operation.

        Args:
            propellant_mass (float): The mass of the propellant.
            thrust (float): The thrust force.
            d_t (float): The time step.
        """
        altitude = self.y[-1] + self.initial_elevation_amsl

        self._append_time(d_t)
        self._update_atmosphere(altitude)
        self._update_vehicle_mass(propellant_mass)
        drag = self._compute_drag()
        y_new, v_new, a_new = self._solve_ballistics_ode(thrust, drag, d_t)
        self._append_flight_states(y_new, v_new, a_new)
        self._update_mach_and_pressure(altitude)
        self._check_rail_exit()

    def _append_time(self, d_t: float) -> None:
        self.t = np.append(self.t, self.t[-1] + d_t)

    def _update_atmosphere(self, altitude: float) -> None:
        self.rho_air = np.append(self.rho_air, self.atmosphere.get_density(altitude))
        self.g = np.append(self.g, self.atmosphere.get_gravity(altitude))

    def _update_vehicle_mass(self, propellant_mass: float) -> None:
        dry = self.rocket.get_dry_mass() + self.motor_dry_mass
        self.vehicle_mass = np.append(self.vehicle_mass, dry + propellant_mass)

    def _compute_drag(self) -> float:
        rho = self.rho_air[-1]
        fus_area = self.rocket.fuselage.frontal_area
        fus_cd = self.rocket.fuselage.get_drag_coefficient()
        rec_cd, rec_area = self.rocket.recovery.get_drag_coefficient_and_area(
            height=self.y,
            time=self.t,
            velocity=self.v,
            propellant_mass=self.vehicle_mass[-1],
        )
        return 0.5 * rho * (fus_area * fus_cd + rec_area * rec_cd)

    def _solve_ballistics_ode(self, thrust: float, drag: float, d_t: float):
        vars0 = {"y": self.y[-1], "v": self.v[-1]}
        results = rk4th_ode_solver(
            variables=vars0,
            equation=ballistics_ode,
            d_t=d_t,
            T=thrust,
            D=drag,
            M=self.vehicle_mass[-1],
            g=self.g[-1],
        )
        return results[0], results[1], results[2]

    def _append_flight_states(self, y: float, v: float, a: float) -> None:
        # ground-impact check
        y = max(y, 0.0) if len(self.y[self.y > 0]) == 0 else y
        self.y = np.append(self.y, y)
        self.v = np.append(self.v, v)
        self.acceleration = np.append(self.acceleration, a)

    def _update_mach_and_pressure(self, altitude: float):
        self.mach_no = np.append(
            self.mach_no, self.atmosphere.get_sonic_velocity(altitude)
        )
        self.P_ext = np.append(
            self.P_ext,
            self.atmosphere.get_pressure(self.y[-1] + self.initial_elevation_amsl),
        )

    def _check_rail_exit(self) -> None:
        if self.velocity_out_of_rail is None and self.y[-1] > self.rail_length:
            self.velocity_out_of_rail = self.v[-2]

    def print_results(self) -> None:
        """
        Print the results of the ballistics operation.
        """
        print("\nROCKET BALLISTICS")

        print(f" Apogee: {np.max(self.y):.2f} m")
        print(f" Max. velocity: {np.max(self.v):.2f} m/s")
        print(f" Max. Mach number: {np.max(self.mach_no):.3f}")
        print(f" Max. acceleration: {np.max(self.acceleration) / 9.81:.2f} gs")
        print(f" Time to apogee: {self.apogee_time:.2f} s")
        print(f" Velocity out of the rail: {self.velocity_out_of_rail:.2f} m/s")
        print(f" Liftoff mass: {self.vehicle_mass[0]:.3f} kg")
        print(f" Flight time: {self.t[-1]:.2f} s")
