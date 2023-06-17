from typing import Optional

import numpy as np

from . import BallisticOperation
from rocketsolver.models.atmosphere import Atmosphere
from rocketsolver.models.rocket import Rocket
from rocketsolver.services.equations import ballistics_ode
from rocketsolver.solvers.odes import rk4th_ode_solver


class Ballistic1DOperation(BallisticOperation):
    """Stores and processes a ballistics operation (aka flight)."""

    def __init__(
        self,
        rocket: Rocket,
        atmosphere: Atmosphere,
        rail_length: float,
        motor_dry_mass: float,
        initial_vehicle_mass: float,
        initial_elevation_amsl: Optional[float] = 0,
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

    def iterate(
        self,
        propellant_mass: float,
        thrust: float,
        d_t: float,
    ) -> None:
        """
        Perform an iteration of the ballistics operation.

        Args:
            propellant_mass (float): The mass of the propellant.
            thrust (float): The thrust force.
            d_t (float): The time step.
        """
        self.t = np.append(self.t, self.t[-1] + d_t)  # append new time value

        self.rho_air = np.append(
            self.rho_air,
            self.atmosphere.get_density(
                y_amsl=(self.y[-1] + self.initial_elevation_amsl)
            ),
        )
        self.g = np.append(
            self.g,
            self.atmosphere.get_gravity(
                self.initial_elevation_amsl + self.y[-1]
            ),
        )

        # Appending the current vehicle mass, consisting of the motor
        # structural mass, mass without the motor, and propellant mass.
        self.vehicle_mass = np.append(
            self.vehicle_mass, propellant_mass + self.rocket.get_dry_mass()
        )

        # Drag properties:
        fuselage_area = self.rocket.fuselage.frontal_area
        fuselage_drag_coeff = self.rocket.fuselage.get_drag_coefficient()
        (
            recovery_drag_coeff,
            recovery_area,
        ) = self.rocket.recovery.get_drag_coefficient_and_area(
            height=self.y,
            time=self.t,
            velocity=self.v,
            propellant_mass=propellant_mass,
        )

        D = (
            (
                fuselage_area * fuselage_drag_coeff
                + recovery_area * recovery_drag_coeff
            )
            * self.rho_air[-1]
            * 0.5
        )

        ballistics_results = rk4th_ode_solver(
            variables={"y": self.y[-1], "v": self.v[-1]},
            equation=ballistics_ode,
            d_t=d_t,
            T=thrust,
            D=D,
            M=self.vehicle_mass[-1],
            g=self.g[-1],
        )

        height = ballistics_results[0]
        velocity = ballistics_results[1]
        acceleration = ballistics_results[2]

        if height < 0 and len(self.y[self.y > 0]) == 0:
            height = 0
            velocity = 0
            acceleration = 0

        self.y = np.append(self.y, height)
        self.v = np.append(self.v, velocity)
        self.acceleration = np.append(self.acceleration, acceleration)

        self.mach_no = np.append(
            self.mach_no,
            self.v[-1]
            / self.atmosphere.get_sonic_velocity(
                self.y[-1] + self.initial_elevation_amsl
            ),
        )

        self.P_ext = np.append(
            self.P_ext,
            self.atmosphere.get_pressure(
                self.y[-1] + self.initial_elevation_amsl
            ),
        )

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
        print(
            f" Velocity out of the rail: {self.velocity_out_of_rail:.2f} m/s"
        )
        print(f" Liftoff mass: {self.vehicle_mass[0]:.3f} kg")
        print(f" Flight time: {self.t[-1]:.2f} s")
