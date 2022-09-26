# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import abstractmethod
from typing import Optional

import numpy as np

from rocketsolver.operations import Operation
from rocketsolver.solvers.srm_internal_ballistics import (
    SRMInternalBallisticsSolver,
)
from rocketsolver.models.propulsion import Motor, SolidMotor
from rocketsolver.utils.isentropic_flow import (
    get_critical_pressure_ratio,
    get_opt_expansion_ratio,
    get_exit_pressure,
    get_operational_correction_factors,
    get_thrust_coefficients,
    get_thrust_from_cf,
    is_flow_choked,
)
from rocketsolver.utils.units import (
    convert_pa_to_psi,
    convert_mass_flux_metric_to_imperial,
)


class MotorOperation(Operation):
    """
    Defines a particular motor operation. Stores and processes all attributes
    obtained from the simulation.
    """

    def __init__(
        self,
        motor: Motor,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
    ) -> None:
        """
        Initializes attributes for the motor operation.
        Each motor category will contain a particular set of attributes.
        """
        self.motor = motor

        self.t = np.array([0])  # time vector

        self.V_0 = np.array(
            [motor.structure.chamber.get_empty_volume()]
        )  # empty chamber volume
        self.optimal_expansion_ratio = np.array([1])  # optimal expansion ratio
        self.m_prop = np.array(
            [motor.initial_propellant_mass]
        )  # propellant mass
        self.P_0 = np.array([initial_pressure])  # chamber stagnation pressure
        self.P_exit = np.array([initial_atmospheric_pressure])  # exit pressure

        # Thrust coefficients and thrust:
        self.C_f = np.array([0])  # thrust coefficient
        self.C_f_ideal = np.array([0])  # ideal thrust coefficient
        self.thrust = np.array([0])  # thrust force (N)

        # If the propellant mass is non zero, 'end_thrust' must be False,
        # since there is still thrust being produced.
        # After the propellant has finished burning and the thrust chamber has
        # stopped producing supersonic flow, 'end_thrust' is changed to True
        # value and the internal ballistics section of the while loop below
        # stops running.
        self.end_thrust = False
        self.end_burn = False

    @abstractmethod
    def iterate(self) -> None:
        """
        Calculates and stores operational parameters in the corresponding
        vectors.

        This method will depend on the motor category. While a SRM will have
        to use/store operational parameters such as burn area and propellant
        volume, a HRE or LRE would not have to.

        When executed, the method must increment the necessary attributes
        according to a differential property (time, distance or other).
        """
        pass

    @abstractmethod
    def print_results(self) -> None:
        """
        Prints results obtained during simulation/operation.
        """
        pass

    @property
    def initial_propellant_mass(self) -> float:
        """
        :return: Initial propellant mass.
        """
        return self.motor.initial_propellant_mass


class SRMOperation(MotorOperation):
    """
    Operation for a Solid Rocket Motor.

    The variable names correspond to what they are commonly reffered to in
    books and papers related to Solid Rocket Propulsion.

    Therefore, PEP8's snake_case will not be followed rigorously.
    """

    def __init__(
        self,
        motor: SolidMotor,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
        ib_solver: Optional[
            SRMInternalBallisticsSolver
        ] = SRMInternalBallisticsSolver(),
    ) -> None:
        """
        Initial parameters for a SRM operation.
        """
        self.ib_solver = ib_solver

        super().__init__(
            motor=motor,
            initial_pressure=initial_pressure,
            initial_atmospheric_pressure=initial_atmospheric_pressure,
        )

        # Grain and propellant parameters:
        self.web = np.array([0])  # instant web thickness
        self.burn_area = np.array(
            [self.motor.grain.get_burn_area(self.web[0])]
        )
        self.propellant_volume = np.array(
            [self.motor.grain.get_burn_area(self.web[0])]
        )
        self.burn_rate = np.array([0])  # burn rate

        # Correction factors:
        self.n_kin = np.array([0])  # kinetics correction factor
        self.n_bl = np.array([0])  # boundary layer correction factor
        self.n_tp = np.array([0])  # two-phase flow correction factor
        self.n_cf = np.array([0])  # thrust coefficient correction factor

    def iterate(
        self,
        d_t: float,
        P_ext: float,
    ) -> None:
        """
        The function uses the Runge-Kutta 4th order numerical method for
        solving the differential equations.
        """
        if self.end_thrust is False:
            self.t = np.append(
                self.t, self.t[-1] + d_t
            )  # append new time value

            self.burn_area = np.append(
                self.burn_area, self.motor.grain.get_burn_area(self.web[-1])
            )
            self.propellant_volume = np.append(
                self.propellant_volume,
                self.motor.grain.get_propellant_volume(self.web[-1]),
            )

            # Calculating the free chamber volume:
            self.V_0 = np.append(
                self.V_0,
                self.motor.get_free_chamber_volume(self.propellant_volume[-1]),
            )
            # Calculating propellant mass:
            self.m_prop = np.append(
                self.m_prop,
                self.propellant_volume[-1] * self.motor.propellant.density,
            )

            # Get burn rate coefficients:
            self.burn_rate = np.append(
                self.burn_rate,
                self.motor.propellant.get_burn_rate(self.P_0[-1]),
            )

            d_x = d_t * self.burn_rate[-1]
            self.web = np.append(self.web, self.web[-1] + d_x)

            self.P_0 = np.append(
                self.P_0,
                self.ib_solver.solve(
                    self.P_0[-1],
                    P_ext,
                    self.burn_area[-1],
                    self.V_0[-1],
                    self.motor.structure.nozzle.get_throat_area(),
                    self.motor.propellant.density,
                    self.motor.propellant.k_mix_ch,
                    self.motor.propellant.R_ch,
                    self.motor.propellant.T0,
                    self.burn_rate[-1],
                    d_t,
                ),
            )

            self.optimal_expansion_ratio = np.append(
                self.optimal_expansion_ratio,
                get_opt_expansion_ratio(
                    self.motor.propellant.k_2ph_ex, self.P_0[-1], P_ext
                ),
            )

            self.P_exit = np.append(
                self.P_exit,
                get_exit_pressure(
                    self.motor.propellant.k_2ph_ex,
                    self.motor.structure.nozzle.expansion_ratio,
                    self.P_0[-1],
                ),
            )

            (
                n_kin_atual,
                n_tp_atual,
                n_bl_atual,
            ) = get_operational_correction_factors(
                self.P_0[-1],
                P_ext,
                convert_pa_to_psi(self.P_0[-1]),
                self.motor.propellant,
                self.motor.structure,
                get_critical_pressure_ratio(self.motor.propellant.k_mix_ch),
                self.V_0[0],
                self.t[-1],
            )

            self.n_kin = np.append(self.n_kin, n_kin_atual)
            self.n_tp = np.append(self.n_tp, n_tp_atual)
            self.n_bl = np.append(self.n_bl, n_bl_atual)

            self.n_cf = np.append(
                self.n_cf,
                (
                    (100 - (n_kin_atual + n_bl_atual + n_tp_atual))
                    * self.motor.structure.nozzle.get_divergent_correction_factor()
                    / 100
                    * self.motor.propellant.combustion_efficiency
                ),
            )

            C_f_atual, C_f_ideal_atual = get_thrust_coefficients(
                self.P_0[-1],
                self.P_exit[-1],
                P_ext,
                self.motor.structure.nozzle.expansion_ratio,
                self.motor.propellant.k_2ph_ex,
                self.n_cf[-1],
            )

            self.C_f = np.append(self.C_f, C_f_atual)
            self.C_f_ideal = np.append(self.C_f_ideal, C_f_ideal_atual)
            self.thrust = np.append(
                self.thrust,
                get_thrust_from_cf(
                    self.C_f[-1],
                    self.P_0[-1],
                    self.motor.structure.nozzle.get_throat_area(),
                ),
            )  # thrust calculation

            if self.m_prop[-1] == 0 and self.end_burn is False:
                self.burn_time = self.t[-1]
                self.end_burn = True

            # This if statement changes 'end_thrust' to True if supersonic
            # flow is not achieved anymore.
            if is_flow_choked(
                self.P_0[-1],
                P_ext,
                get_critical_pressure_ratio(self.motor.propellant.k_mix_ch),
            ):
                self.thrust_time = self.t[-1]
                self.end_thrust = True

    def print_results(self) -> None:
        print("\nBURN REGRESSION")
        if self.m_prop[0] > 1:
            print(f" Propellant initial mass {self.m_prop[0]:.3f} kg")
        else:
            print(f" Propellant initial mass {self.m_prop[0] * 1e3:.3f} g")
        print(" Mean Kn: %.2f" % np.mean(self.klemmung))
        print(" Max Kn: %.2f" % np.max(self.klemmung))
        print(
            f" Initial to final Kn ratio: {self.initial_to_final_klemmung_ratio:.3f}"
        )
        print(f" Volumetric efficiency: {self.volumetric_efficiency:.3%}")
        print(" Burn profile: " + self.burn_profile)
        print(
            f" Max initial mass flux: {self.max_mass_flux:.3f} kg/s-m-m or "
            f"{convert_mass_flux_metric_to_imperial(self.max_mass_flux):.3f} "
            "lb/s-in-in"
        )

        print("\nCHAMBER PRESSURE")
        print(
            f" Maximum, average chamber pressure: {np.max(self.P_0) * 1e-6:.3f}, "
            f"{np.mean(self.P_0) * 1e-6:.3f} MPa"
        )

        print("\nTHRUST AND IMPULSE")
        print(
            f" Maximum, average thrust: {np.max(self.thrust):.3f}, {np.mean(self.thrust):.3f} N"
        )
        print(
            f" Total, specific impulses: {self.total_impulse:.3f} N-s, {self.specific_impulse:.3f} s"
        )
        print(
            f" Burnout time, thrust time: {self.burn_time:.3f}, {self.thrust_time:.3f} s"
        )

        print("\nNOZZLE DESIGN")
        print(f" Average nozzle efficiency: {np.mean(self.n_cf):.3%}")

    @property
    def klemmung(self) -> np.ndarray:
        return (
            self.burn_area[self.burn_area > 0]
            / self.motor.structure.nozzle.get_throat_area()
        )

    @property
    def initial_to_final_klemmung_ratio(self) -> float:
        return self.klemmung[0] / self.klemmung[-1]

    @property
    def volumetric_efficiency(self) -> float:
        return (
            self.propellant_volume[0]
            / self.motor.structure.chamber.get_empty_volume()
        )

    @property
    def burn_profile(self, deviancy: Optional[float] = 0.02) -> str:
        """
        Returns string with burn profile.
        """
        burn_area = self.burn_area[self.burn_area > 0]

        if burn_area[0] / burn_area[-1] > 1 + deviancy:
            return "regressive"
        elif burn_area[0] / burn_area[-1] < 1 - deviancy:
            return "progressive"
        else:
            return "neutral"

    @property
    def max_mass_flux(self) -> float:
        return np.max(self.grain_mass_flux)

    @property
    def grain_mass_flux(self) -> np.ndarray:
        return self.motor.grain.get_mass_flux_per_segment(
            self.burn_rate,
            self.motor.propellant.density,
            self.web,
        )

    @property
    def total_impulse(self) -> float:
        return np.mean(self.thrust) * self.t[-1]

    @property
    def specific_impulse(self) -> float:
        return self.total_impulse / self.m_prop[0] / 9.81
