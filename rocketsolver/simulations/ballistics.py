# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from rocketsolver.models.atmosphere import Atmosphere
from rocketsolver.models.recovery import Recovery
from rocketsolver.models.rocket import Rocket
from rocketsolver.operations.ballistics import Ballistic1DOperation
from rocketsolver.simulations import Simulation


class BallisticSimulation(Simulation):
    def __init__(
        self,
        thrust: np.ndarray,
        motor_dry_mass: float,
        initial_propellant_mass: float,
        time: np.ndarray,
        rocket: Rocket,
        recovery: Recovery,
        atmosphere: Atmosphere,
        d_t: float,
        initial_elevation_amsl: float,
        rail_length: float,
    ) -> None:
        self.thrust = thrust
        self.initial_propellant_mass = initial_propellant_mass
        self.motor_dry_mass = motor_dry_mass
        self.time = time
        self.rocket = rocket
        self.recovery = recovery
        self.atmosphere = atmosphere
        self.d_t = d_t
        self.initial_elevation_amsl = initial_elevation_amsl
        self.rail_length = rail_length

        self.t = np.array([0])

    def get_propellant_mass(self) -> np.ndarray:
        prop_mass = np.array([])

        for time in self.time:
            prop_mass = np.append(
                prop_mass,
                self.initial_propellant_mass
                * (self.time[-1] - time)
                / self.time[-1],
            )

        return prop_mass

    def run(self) -> tuple[np.array, Ballistic1DOperation]:
        """
        Runs the main loop of the simulation, returning all the internal and
        external ballistics parameters.
        """
        self.ballistic_operation = Ballistic1DOperation(
            self.rocket,
            self.recovery,
            self.atmosphere,
            rail_length=self.rail_length,
            motor_dry_mass=self.motor_dry_mass,
            initial_vehicle_mass=self.rocket.structure.mass_without_motor
            + self.motor_dry_mass
            + self.initial_propellant_mass,
            initial_elevation_amsl=self.initial_elevation_amsl,
        )

        propellant_mass = self.get_propellant_mass()

        i = 0

        while self.ballistic_operation.y[i] >= 0:
            self.t = np.append(self.t, self.t[i] + self.d_t)  # new time value

            thrust = np.interp(
                self.t[-1],
                self.time,
                self.thrust,
                left=0,
                right=0,
            )  # interpolating thrust with new time value

            self.ballistic_operation.iterate(
                np.interp(
                    self.t[-1],
                    self.time,
                    propellant_mass,
                    left=0,
                    right=0,
                ),  # interpolating propellant mass with new time value
                thrust,
                self.d_t,
            )

            i += 1

        return (self.t, self.ballistic_operation)

    def print_results(self):
        """
        Prints the results of the simulation.
        """
        print("\nINTERNAL BALLISTICS COUPLED SIMULATION RESULTS")
        self.ballistic_operation.print_results()
