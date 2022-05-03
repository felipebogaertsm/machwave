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

import fluids.atmosphere as atm
import numpy as np

from models.atmosphere import Atmosphere
from models.motor import Motor
from models.recovery import Recovery
from models.rocket import Rocket
from simulations import Simulation
from simulations.dataclasses.ballistics import Ballistics
from simulations.dataclasses.internal_ballistics import InternalBallistics
from solvers.srm_internal_ballistics import (
    SRMInternalBallisticsSolver,
)
from solvers.ballistics_1d import Ballistics1D
from utils.isentropic_flow import (
    get_critical_pressure_ratio,
    get_divergent_correction_factor,
    get_opt_expansion_ratio,
    get_exit_pressure,
    get_operational_correction_factors,
    get_thrust_coefficients,
    get_impulses,
    get_thrust_from_cf,
    is_flow_choked,
)
from utils.odes import solve_cp_seidel, ballistics_ode
from utils.units import convert_pa_to_psi


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

        # INITIAL CONDITIONS
        web = np.array([0])
        t = np.array([0])
        P_ext = np.array([])
        rho_air = np.array([])
        g = np.array([])
        P_0 = np.array([self.igniter_pressure])
        P_0_psi = np.array([convert_pa_to_psi(self.igniter_pressure)])
        P_exit = np.array([])
        y = np.array([0])
        v = np.array([0])
        mach_no = np.array([0])

        # ALLOCATING NUMPY ARRAYS FOR FUTURE CALCULATIONS
        vehicle_mass = np.array([])  # total mass of the vehicle
        burn_rate = np.array([])  # burn rate
        V_0 = np.array([])  # empty chamber volume
        optimal_expansion_ratio = np.array([])  # opt. expansion ratio
        A_burn = np.array([])  # burn area
        V_prop = np.array([])  # propellant volume
        m_prop = np.array([])  # propellant mass
        n_kin, n_bl, n_tp, n_cf = (
            np.array([]),
            np.array([]),
            np.array([]),
            np.array([]),
        )  # thrust coefficient correction factors
        C_f, C_f_ideal, T = (
            np.array([]),
            np.array([]),
            np.array([]),
        )  # thrust coefficient and thrust

        # PRE CALCULATIONS
        # Critical pressure ratio:
        critical_pressure_ratio = get_critical_pressure_ratio(
            self.motor.propellant.k_mix_ch
        )
        # Divergent correction factor:
        n_div = get_divergent_correction_factor(
            self.motor.structure.nozzle.divergent_angle
        )
        # Variables storing the apogee, apogee time and main chute ejection time:
        apogee, apogee_time, main_time = 0, -1, 0
        # Calculation of empty chamber volume (constant throughout the operation):
        empty_chamber_volume = self.motor.structure.chamber.get_empty_volume()

        # If the propellant mass is non zero, 'end_thrust' must be False,
        # since there is still thrust being produced.

        # After the propellant has finished burning and the thrust chamber has
        # stopped producing supersonic flow, 'end_thrust' is changed to a
        # True value and the internal ballistics section of the while loop below
        # stops running.

        end_thrust = False
        end_burn = False

        i = 0

        while y[i] >= 0 or m_prop[i - 1] > 0:
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

            if end_thrust is False:  # while motor is producing thrust
                A_burn, V_prop = (
                    np.append(A_burn, self.motor.grain.get_burn_area(web[i])),
                    np.append(
                        V_prop, self.motor.grain.get_propellant_volume(web[i])
                    ),
                )

                # Calculating the free chamber volume:
                V_0 = np.append(V_0, empty_chamber_volume - V_prop[i])
                # Calculating propellant mass:
                m_prop = np.append(
                    m_prop, V_prop[i] * self.motor.propellant.density
                )

                # Get burn rate coefficients:
                burn_rate = np.append(
                    burn_rate, self.motor.propellant.get_burn_rate(P_0[i])
                )

                d_x = self.d_t * burn_rate[i]
                web = np.append(web, web[i] + d_x)

                ib_solver = SRMInternalBallisticsSolver()

                P_0 = np.append(
                    P_0,
                    ib_solver.solve(
                        P_0[i],
                        P_ext[i],
                        A_burn[i],
                        V_0[i],
                        self.motor.structure.nozzle.get_throat_area(),
                        self.motor.propellant.density,
                        self.motor.propellant.k_mix_ch,
                        self.motor.propellant.R_ch,
                        self.motor.propellant.T0,
                        burn_rate[i],
                        self.d_t,
                    ),
                )
                P_0_psi = np.append(P_0_psi, convert_pa_to_psi(P_0[i]))

                optimal_expansion_ratio = np.append(
                    optimal_expansion_ratio,
                    get_opt_expansion_ratio(
                        self.motor.propellant.k_2ph_ex, P_0[i], P_ext[i]
                    ),
                )

                P_exit = np.append(
                    P_exit,
                    get_exit_pressure(
                        self.motor.propellant.k_2ph_ex,
                        self.motor.structure.nozzle.expansion_ratio,
                        P_0[i],
                    ),
                )

                (
                    n_kin_atual,
                    n_tp_atual,
                    n_bl_atual,
                ) = get_operational_correction_factors(
                    P_0[i],
                    P_ext[i],
                    P_0_psi[i],
                    self.motor.propellant,
                    self.motor.structure,
                    critical_pressure_ratio,
                    V_0[0],
                    t[i],
                )

                n_kin = np.append(n_kin, n_kin_atual)
                n_tp = np.append(n_tp, n_tp_atual)
                n_bl = np.append(n_bl, n_bl_atual)

                n_cf = np.append(
                    n_cf,
                    (
                        (100 - (n_kin_atual + n_bl_atual + n_tp_atual))
                        * n_div
                        / 100
                        * self.motor.propellant.combustion_efficiency
                    ),
                )

                C_f_atual, C_f_ideal_atual = get_thrust_coefficients(
                    P_0[i],
                    P_exit[i],
                    P_ext[i],
                    self.motor.structure.nozzle.expansion_ratio,
                    self.motor.propellant.k_2ph_ex,
                    n_cf[i],
                )

                C_f = np.append(C_f, C_f_atual)
                C_f_ideal = np.append(C_f_ideal, C_f_ideal_atual)
                T = np.append(
                    T,
                    get_thrust_from_cf(
                        C_f[i],
                        self.motor.structure.nozzle.get_throat_area(),
                        P_0[i],
                    ),
                )  # thrust calculation

                if m_prop[i] == 0 and end_burn is False:
                    t_burnout = t[i]
                    end_burn = True

                # This if statement changes 'end_thrust' to True if supersonic
                # flow is not achieved anymore.
                if is_flow_choked(P_0[i], P_ext[i], critical_pressure_ratio):
                    t_thrust = t[i]
                    self.d_t = self.d_t * self.dd_t
                    T_mean = np.mean(T)
                    end_thrust = True

            # This else statement is necessary since the thrust and propellant
            # mass arrays are still being used inside the main while loop.
            # Therefore, it is necessary to append 0 to these arrays for the
            # ballistic part of the while loop to work correctly.
            else:
                m_prop = np.append(m_prop, 0)
                T = np.append(T, 0)

            # Entering first value for the vehicle mass and acceleration:
            if i == 0:
                vehicle_mass_initial = (
                    m_prop[0]
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
                            + m_prop[0]
                        )
                    ]
                )

            # Appending the current vehicle mass, consisting of the motor
            # structural mass, mass without the motor and propellant mass.
            vehicle_mass = np.append(
                vehicle_mass,
                m_prop[i]
                + self.motor.structure.dry_mass
                + self.rocket.structure.mass_without_motor,
            )

            # Drag properties:
            fuselage_area = self.rocket.fuselage.frontal_area
            fuselage_drag_coeff = self.rocket.fuselage.drag_coefficient
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

            ballistics_solver = Ballistics1D()
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
                mach_no, v[i] / atm.ATMOSPHERE_1976(y[i]).v_sonic
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

        ballistics = Ballistics(
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
        )

        optimal_grain_length = self.motor.grain.get_optimal_segment_length()
        initial_port_to_throat = (self.motor.grain.core_diameter[-1] ** 2) / (
            self.motor.structure.nozzle.throat_diameter ** 2
        )

        burn_profile = self.motor.grain.get_burn_profile(A_burn[A_burn != 0.0])
        Kn = A_burn / self.motor.structure.nozzle.get_throat_area()
        Kn_non_zero = Kn[Kn != 0.0]
        initial_to_final_kn = Kn_non_zero[0] / Kn_non_zero[-1]
        grain_mass_flux = self.motor.grain.get_mass_flux_per_segment(
            burn_rate, self.motor.propellant.density, web
        )

        ib_parameters = InternalBallistics(
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
            empty_chamber_volume,
            initial_to_final_kn,
            P_exit,
        )

        return ballistics, ib_parameters
