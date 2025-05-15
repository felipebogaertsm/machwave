import numpy as np

from machwave.models.propulsion.motors import SolidMotor
from machwave.operations.internal_ballistics.base import MotorOperation
from machwave.services.conversions import (
    convert_mass_flux_metric_to_imperial,
    convert_pa_to_psi,
)
from machwave.services.equations import solve_cp_seidel
from machwave.services.flow.isentropic import (
    get_critical_pressure_ratio,
    get_exit_pressure,
    get_operational_correction_factors,
    get_thrust_coefficients,
    get_thrust_from_cf,
    is_flow_choked,
)
from machwave.solvers.odes import rk4th_ode_solver


class SolidMotorOperation(MotorOperation):
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

        self.motor: SolidMotor = motor

        # Grain and propellant parameters:
        self.V_0 = np.array(
            [motor.thrust_chamber.combustion_chamber.internal_volume]
        )  # empty chamber volume
        self.web = np.array([0])  # instant web thickness
        self.burn_area = np.array([self.motor.grain.get_burn_area(self.web[0])])
        self.propellant_volume = np.array(
            [self.motor.grain.get_propellant_volume(self.web[0])]
        )
        self.burn_rate = np.array([0])  # burn rate

        # Correction factors:
        self.n_kin = np.array([0])  # kinetics correction factor
        self.n_bl = np.array([0])  # boundary layer correction factor
        self.n_tp = np.array([0])  # two-phase flow correction factor
        self.n_cf = np.array([0])  # thrust coefficient correction factor

    def run_timestep(
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
        if self.end_thrust:
            return

        self._append_time(d_t)
        self._update_grain_geometry()
        self._update_chamber_volume_and_mass()
        self._compute_pressure(d_t, P_ext)
        self._compute_flow(P_ext)
        self._check_burn_end()
        self._check_thrust_end(P_ext)

    def _append_time(self, d_t: float) -> None:
        self.t = np.append(self.t, self.t[-1] + d_t)

    def _update_grain_geometry(self) -> None:
        web_last = self.web[-1]
        area = self.motor.grain.get_burn_area(web_last)
        vol = self.motor.grain.get_propellant_volume(web_last)
        self.burn_area = np.append(self.burn_area, area)
        self.propellant_volume = np.append(self.propellant_volume, vol)
        self.burn_rate = np.append(
            self.burn_rate,
            self.motor.propellant.get_burn_rate(self.P_0[-1]),
        )
        dx = self.burn_rate[-1] * (self.t[-1] - self.t[-2])
        self.web = np.append(self.web, web_last + dx)

    def _update_chamber_volume_and_mass(self) -> None:
        free_vol = self.motor.get_free_chamber_volume(self.propellant_volume[-1])
        self.V_0 = np.append(self.V_0, free_vol)
        m_prop = self.propellant_volume[-1] * self.motor.propellant.density
        self.m_prop = np.append(self.m_prop, m_prop)

    def _compute_pressure(self, d_t: float, P_ext: float) -> None:
        new_P = rk4th_ode_solver(
            variables={"P0": self.P_0[-1]},
            equation=solve_cp_seidel,
            d_t=d_t,
            Pe=P_ext,
            Ab=self.burn_area[-1],
            V0=self.V_0[-1],
            At=self.motor.thrust_chamber.nozzle.get_throat_area(),
            pp=self.motor.propellant.density,
            k=self.motor.propellant.k_mix,
            R=self.motor.propellant.R_ch,
            T0=self.motor.propellant.T0,
            r=self.burn_rate[-1],
        )[0]
        self.P_0 = np.append(self.P_0, new_P)
        exit_P = get_exit_pressure(
            self.motor.propellant.k_ex,
            self.motor.thrust_chamber.nozzle.expansion_ratio,
            new_P,
        )
        self.P_exit = np.append(self.P_exit, exit_P)

    def _compute_flow(self, P_ext: float) -> None:
        P0 = self.P_0[-1]
        tex = convert_pa_to_psi(P0)
        n_kin, n_tp, n_bl = get_operational_correction_factors(
            P0,
            P_ext,
            tex,
            self.motor.propellant,
            self.motor.thrust_chamber,
            get_critical_pressure_ratio(self.motor.propellant.k_mix),
            self.V_0[0],
            self.t[-1],
        )
        self.n_kin = np.append(self.n_kin, n_kin)
        self.n_tp = np.append(self.n_tp, n_tp)
        self.n_bl = np.append(self.n_bl, n_bl)
        cf_corr = (
            (100 - (n_kin + n_tp + n_bl))
            * self.motor.thrust_chamber.nozzle.get_divergent_correction_factor()
            / 100
            * self.motor.propellant.combustion_efficiency
        )
        self.n_cf = np.append(self.n_cf, cf_corr)
        cf, cf_ideal = get_thrust_coefficients(
            P0,
            self.P_exit[-1],
            P_ext,
            self.motor.thrust_chamber.nozzle.expansion_ratio,
            self.motor.propellant.k_ex,
            cf_corr,
        )
        self.C_f = np.append(self.C_f, cf)
        self.C_f_ideal = np.append(self.C_f_ideal, cf_ideal)
        thrust = get_thrust_from_cf(
            cf, P0, self.motor.thrust_chamber.nozzle.get_throat_area()
        )
        self.thrust = np.append(self.thrust, thrust)

    def _check_burn_end(self) -> None:
        if self.m_prop[-1] <= 0 and not self.end_burn:
            self.burn_time = self.t[-1]
            self.end_burn = True

    def _check_thrust_end(self, P_ext: float) -> None:
        if not is_flow_choked(
            self.P_0[-1],
            P_ext,
            get_critical_pressure_ratio(self.motor.propellant.k_mix),
        ):
            self._thrust_time = self.t[-1]
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
        print(f" Initial to final Kn ratio: {self.initial_to_final_klemmung_ratio:.3f}")
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
            / self.motor.thrust_chamber.nozzle.get_throat_area()
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
            / self.motor.thrust_chamber.combustion_chamber.internal_volume
        )

    @property
    def burn_profile(self, deviancy: float = 0.02) -> str:
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
