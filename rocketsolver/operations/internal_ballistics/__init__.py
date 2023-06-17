from abc import abstractmethod
from typing import Optional

import numpy as np

from rocketsolver.operations import Operation
from rocketsolver.solvers.odes import rk4th_ode_solver
from rocketsolver.services.equations import solve_cp_seidel
from rocketsolver.models.propulsion import Motor, SolidMotor
from rocketsolver.services.isentropic_flow import (
    get_critical_pressure_ratio,
    get_exit_pressure,
    get_operational_correction_factors,
    get_thrust_coefficients,
    get_thrust_from_cf,
    is_flow_choked,
)
from rocketsolver.services.conversions import (
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
            [motor.structure.chamber.empty_volume]
        )  # empty chamber volume
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
        Get the initial propellant mass.

        Returns:
            float: The initial propellant mass.
        """
        return self.motor.initial_propellant_mass


class SRMOperation(MotorOperation):
    """
    Operation for a Solid Rocket Motor.

    The variable names correspond to what they are commonly referred to in
    books and papers related to Solid Rocket Propulsion.

    Therefore, PEP8's snake_case will not be followed rigorously.
    """

    def __init__(
        self,
        motor: SolidMotor,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
    ) -> None:
        """
        Initial parameters for a SRM operation.
        """
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
            [self.motor.grain.get_propellant_volume(self.web[0])]
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
        Iterate the motor operation by calculating and storing operational
        parameters in the corresponding vectors.

        Args:
            d_t (float): The time increment.
            P_ext (float): The external pressure.
        """
        if not self.end_thrust:
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
                rk4th_ode_solver(
                    variables={"P0": self.P_0[-1]},
                    equation=solve_cp_seidel,
                    d_t=d_t,
                    Pe=P_ext,
                    Ab=self.burn_area[-1],
                    V0=self.V_0[-1],
                    At=self.motor.structure.nozzle.get_throat_area(),
                    pp=self.motor.propellant.density,
                    k=self.motor.propellant.k_mix_ch,
                    R=self.motor.propellant.R_ch,
                    T0=self.motor.propellant.T0,
                    r=self.burn_rate[-1],
                )[0],
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

            if self.m_prop[-1] == 0 and not self.end_burn:
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
        """
        Prints the results obtained during the SRM operation.
        """
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
        """
        Get the klemmung values.

        Returns:
            np.ndarray: The klemmung values.
        """
        return (
            self.burn_area[self.burn_area > 0]
            / self.motor.structure.nozzle.get_throat_area()
        )

    @property
    def initial_to_final_klemmung_ratio(self) -> float:
        """
        Get the ratio of the initial to final klemmung.

        Returns:
            float: The ratio of the initial to final klemmung.
        """
        return self.klemmung[0] / self.klemmung[-1]

    @property
    def volumetric_efficiency(self) -> float:
        """
        Get the volumetric efficiency.

        Returns:
            float: The volumetric efficiency.
        """
        return (
            self.propellant_volume[0]
            / self.motor.structure.chamber.empty_volume
        )

    @property
    def burn_profile(self, deviancy: Optional[float] = 0.02) -> str:
        """
        Get the burn profile.

        Args:
            deviancy (float, optional): The deviancy threshold for determining the burn profile.
                Defaults to 0.02.

        Returns:
            str: The burn profile ("regressive", "progressive", or "neutral").
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
        """
        Get the maximum mass flux.

        Returns:
            float: The maximum mass flux.
        """
        return np.max(self.grain_mass_flux)

    @property
    def grain_mass_flux(self) -> np.ndarray:
        """
        Get the grain mass flux.

        Returns:
            np.ndarray: The grain mass flux.
        """
        return self.motor.grain.get_mass_flux_per_segment(
            self.burn_rate,
            self.motor.propellant.density,
            self.web,
        )

    @property
    def total_impulse(self) -> float:
        """
        Get the total impulse.

        Returns:
            float: The total impulse.
        """
        return np.mean(self.thrust) * self.t[-1]

    @property
    def specific_impulse(self) -> float:
        """
        Get the specific impulse.

        Returns:
            float: The specific impulse.
        """
        return self.total_impulse / self.m_prop[0] / 9.81
