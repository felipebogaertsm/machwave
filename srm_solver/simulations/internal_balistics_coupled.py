# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
The coupled internal ballistics simulation calculates both internal and 
external ballistics parameters simulatneously. 

The main advantage of this strategy is that, while some environmental 
attributes change during flight, they also serve as inputs for the internal 
ballistic of the motor. The main attribute that changes during flight is the 
ambient pressure, which impacts the propellant burn rate inside the motor.
"""

import numpy as np

from models.atmosphere import Atmosphere
from models.propulsion import Motor, SolidMotor
from models.recovery import Recovery
from models.rocket import Rocket
from simulations import Simulation
from simulations.dataclasses.ballistics import Ballistics
from simulations.dataclasses.internal_ballistics import SRMInternalBallistics
from simulations.operations.ballistics import BallisticsOperation
from simulations.operations.internal_ballistics import SRMOperation
from solvers.srm_internal_ballistics import (
    SRMInternalBallisticsSolver,
)
from solvers.ballistics_1d import Ballistics1D
from utils.isentropic_flow import (
    get_critical_pressure_ratio,
    get_impulses,
)
from utils.utilities import get_burn_profile


class InternalBallisticsCoupled(Simulation):
    def __init__(
        self,
        motor: Motor,
        rocket: Rocket,
        recovery: Recovery,
        atmosphere: Atmosphere,
        d_t: float,
        dd_t: float,
        initial_elevation_amsl: float,
        igniter_pressure: float,
        rail_length: float,
    ) -> None:
        self.motor = motor
        self.rocket = rocket
        self.recovery = recovery
        self.atmosphere = atmosphere
        self.d_t = d_t
        self.dd_t = dd_t
        self.initial_elevation_amsl = initial_elevation_amsl
        self.igniter_pressure = igniter_pressure
        self.rail_length = rail_length

    def run(self):
        """
        Runs the main loop of the simulation, returning all the internal and
        external ballistics parameters as instances of the InternalBallistics
        and Ballistics classes.

        The function uses the Runge-Kutta 4th order numerical method for
        solving the differential equations.

        The variable names correspond to what they are commonly reffered to in
        books and papers related to Solid Rocket Propulsion.

        Therefore, PEP8's snake_case will not be followed rigorously.
        """

        # Defining operations and solvers for the simulation:
        if isinstance(self.motor, SolidMotor):
            ib_solver = SRMInternalBallisticsSolver()
            motor_operation = SRMOperation()

        ballistics_solver = Ballistics1D()
        ballistic_operation = BallisticsOperation()

        # PRE CALCULATIONS
        critical_pressure_ratio = get_critical_pressure_ratio(
            self.motor.propellant.k_mix_ch
        )
        # Variables storing the apogee, apogee time:
        apogee, apogee_time = 0, -1

        # If the propellant mass is non zero, 'end_thrust' must be False,
        # since there is still thrust being produced.
        # After the propellant has finished burning and the thrust chamber has
        # stopped producing supersonic flow, 'end_thrust' is changed to True
        # value and the internal ballistics section of the while loop below
        # stops running.

        end_thrust = False
        end_burn = False

        i = 0

        while y[i] >= 0 or motor_operation.m_prop[i - 1] > 0:
            t = np.append(t, t[i] + self.d_t)  # append new time value

            # Obtaining the value for the air density, the acceleration of
            # gravity and ext. pressure in function of the current altitude.
            rho_air = np.append(
                rho_air,
                self.atmosphere.get_density(
                    y_amsl=(y[i] + self.initial_elevation_amsl)
                ),
            )
            g = np.append(
                g,
                self.atmosphere.get_gravity(
                    self.initial_elevation_amsl + y[i]
                ),
            )
            P_ext = np.append(
                P_ext,
                self.atmosphere.get_pressure(
                    self.initial_elevation_amsl + y[i]
                ),
            )

            motor_operation.iterate(self.d_t, P_ext)

            # Entering first value for the vehicle mass and acceleration:
            if i == 0:
                vehicle_mass_initial = (
                    motor_operation.m_prop[0]
                    + self.rocket.structure.mass_without_motor
                    + self.motor.structure.dry_mass
                )
                vehicle_mass = np.append(vehicle_mass, vehicle_mass_initial)
                acc = np.array(
                    [
                        T[0]
                        / (
                            self.rocket.structure.mass_without_motor
                            + self.motor.structure.dry_mass
                            + motor_operation.m_prop[0]
                        )
                    ]
                )

            # Appending the current vehicle mass, consisting of the motor
            # structural mass, mass without the motor and propellant mass.
            vehicle_mass = np.append(
                vehicle_mass,
                motor_operation.m_prop[i]
                + self.motor.structure.dry_mass
                + self.rocket.structure.mass_without_motor,
            )

            # Drag properties:
            fuselage_area = self.rocket.fuselage.frontal_area
            fuselage_drag_coeff = self.rocket.fuselage.get_drag_coefficient()
            (
                recovery_drag_coeff,
                recovery_area,
            ) = self.recovery.get_drag_coefficient_and_area(
                height=y, time=t, velocity=v, propellant_mass=m_prop
            )

            D = (
                (
                    fuselage_area * fuselage_drag_coeff
                    + recovery_area * recovery_drag_coeff
                )
                * rho_air[i]
                * 0.5
            )

            ballistics_results = ballistics_solver.solve(
                y[i],
                v[i],
                T[i],
                D,
                vehicle_mass[i],
                g[i],
                self.d_t,
            )

            y = np.append(y, ballistics_results[0])
            v = np.append(v, ballistics_results[1])
            acc = np.append(acc, ballistics_results[2])

            mach_no = np.append(
                mach_no, v[i] / self.atmosphere.get_sonic_velocity(y[i])
            )

            if y[i + 1] <= y[i] and m_prop[i] == 0 and apogee == 0:
                apogee = y[i]
                apogee_time = t[np.where(y == apogee)]

            i += 1

        if y[-1] < 0:
            y = np.delete(y, -1)
            v = np.delete(v, -1)
            acc = np.delete(acc, -1)
            t = np.delete(t, -1)

        v_rail = v[np.where(y >= self.rail_length)]
        v_rail = v_rail[0]
        y_burnout = y[np.where(v == np.max(v))]
        y_burnout = y_burnout[0]
        flight_time = t[-1]

        nozzle_eff = C_f / C_f_ideal  # nozzle efficiency

        I_total, I_sp = get_impulses(T_mean, t, t_burnout, m_prop)

        optimal_grain_length = [
            segment.get_optimal_length()
            for segment in self.motor.grain.segments
        ]
        initial_port_to_throat = (
            self.motor.grain.segments[-1].core_diameter ** 2
        ) / (self.motor.structure.nozzle.throat_diameter ** 2)

        burn_profile = get_burn_profile(burn_area=A_burn[A_burn != 0.0])
        Kn = A_burn / self.motor.structure.nozzle.get_throat_area()
        Kn_non_zero = Kn[Kn != 0.0]
        initial_to_final_kn = Kn_non_zero[0] / Kn_non_zero[-1]
        grain_mass_flux = self.motor.grain.get_mass_flux_per_segment(
            burn_rate, self.motor.propellant.density, web
        )

        return (
            Ballistics(
                t,
                y,
                v,
                acc,
                v_rail,
                y_burnout,
                mach_no,
                apogee_time[0],
                flight_time,
                P_ext,
            ),
            SRMInternalBallistics(
                t,
                P_0,
                T,
                T_mean,
                I_total,
                I_sp,
                t_burnout,
                t_thrust,
                nozzle_eff,
                optimal_expansion_ratio,
                V_prop,
                A_burn,
                Kn,
                m_prop,
                grain_mass_flux,
                optimal_grain_length,
                initial_port_to_throat,
                burn_profile,
                self.motor.structure.chamber.get_empty_volume(),
                initial_to_final_kn,
                P_exit,
            ),
        )
