import numpy as np

from machwave.models.propulsion.motors import LiquidEngine
from machwave.operations.internal_ballistics.base import MotorOperation
from machwave.services.equations import solve_pressure_fed_lre_chamber_pressure
from machwave.services.flow.isentropic import (
    get_critical_pressure_ratio,
    get_exit_pressure,
    get_thrust_coefficients,
    get_thrust_from_cf,
    is_flow_choked,
)
from machwave.solvers.odes import rk4th_ode_solver


class LiquidEngineOperation(MotorOperation):
    """
    Operation for a Liquid Rocket Engine.

    The variable names correspond to what they are commonly referred to in books and papers related to
    Rocket Propulsion. Therefore, PEP8's snake_case will not be followed rigorously.
    """

    motor: LiquidEngine

    def __init__(
        self,
        motor: LiquidEngine,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
    ) -> None:
        """
        Initial parameters for a LRE operation.
        """
        super().__init__(
            motor=motor,
            initial_pressure=initial_pressure,
            initial_atmospheric_pressure=initial_atmospheric_pressure,
        )

        self.oxidizer_mass = np.array([motor.feed_system.oxidizer_tank.fluid_mass])
        self.fuel_mass = np.array([motor.feed_system.fuel_tank.fluid_mass])
        self.n_cf = np.array([1.0])  # thrust coefficient correction factor

        self.fuel_tank_pressure = np.array([motor.feed_system.fuel_tank.get_pressure()])
        self.oxidizer_tank_pressure = np.array(
            [motor.feed_system.oxidizer_tank.get_pressure()]
        )

    def run_timestep(
        self,
        d_t: float,
        P_ext: float,
    ) -> None:
        """
        Advance simulation by time step d_t under external pressure P_ext.

        Args:
            d_t: Time step.
            P_ext: External pressure.
        """
        if self.end_thrust:
            return

        self._append_time(d_t)
        m_dot_fuel, m_dot_ox = self._compute_nominal_mass_flows()
        m_dot_fuel, m_dot_ox = self._clamp_mass_flows(m_dot_fuel, m_dot_ox, d_t)
        m_dot_fuel, m_dot_ox = self._adjust_flows_for_stoichiometry(
            m_dot_fuel, m_dot_ox, d_t
        )
        self._update_propellant_properties()

        new_P = self._compute_chamber_pressure(d_t, m_dot_fuel, m_dot_ox)
        self._append_chamber_pressure(new_P)
        P_exit = self._compute_exit_pressure()
        self._append_exit_pressure(P_exit)
        self._append_cf_correction(1.0)
        cf, cf_ideal = self._compute_thrust_coefficients(P_exit, P_ext)
        self._append_thrust(cf, cf_ideal)

        self._update_propellant_masses(m_dot_fuel, m_dot_ox, d_t)
        self._update_tank_pressures()
        self._check_burn_end()
        self._check_thrust_end(P_ext)

    def _append_time(self, d_t: float) -> None:
        self.t = np.append(self.t, self.t[-1] + d_t)

    def _update_propellant_properties(self) -> None:
        self.motor.propellant.update_properties(
            chamber_pressure=self.P_0[-1],
            eps=self.motor.thrust_chamber.nozzle.expansion_ratio,
        )

    def _compute_nominal_mass_flows(self) -> tuple[float, float]:
        if self.m_prop[-1] > 0:
            fuel_flow = self.motor.feed_system.get_mass_flow_fuel(
                chamber_pressure=self.P_0[-1],
                discharge_coefficient=self.motor.thrust_chamber.injector.discharge_coefficient_fuel,
                injector_area=self.motor.thrust_chamber.injector.area_fuel,
            )
            ox_flow = self.motor.feed_system.get_mass_flow_ox(
                chamber_pressure=self.P_0[-1],
                discharge_coefficient=self.motor.thrust_chamber.injector.discharge_coefficient_oxidizer,
                injector_area=self.motor.thrust_chamber.injector.area_ox,
            )
        else:
            fuel_flow = ox_flow = 0.0
        return fuel_flow, ox_flow

    def _clamp_mass_flows(
        self, m_dot_fuel: float, m_dot_ox: float, d_t: float
    ) -> tuple[float, float]:
        max_fuel_rate = self.fuel_mass[-1] / d_t
        max_ox_rate = self.oxidizer_mass[-1] / d_t
        return min(m_dot_fuel, max_fuel_rate), min(m_dot_ox, max_ox_rate)

    def _adjust_flows_for_stoichiometry(
        self, m_dot_fuel: float, m_dot_ox: float, d_t: float
    ) -> tuple[float, float]:
        of = self.motor.propellant.of_ratio
        fuel_last = self.fuel_mass[-1]
        ox_last = self.oxidizer_mass[-1]
        # convert to consumed mass this step
        cons_f = m_dot_fuel * d_t
        cons_o = m_dot_ox * d_t
        # limiting reagent
        if cons_f >= fuel_last:
            cons_f = fuel_last
            cons_o = of * cons_f
            self.end_burn = True
            self.burn_time = self.t[-1]
        elif cons_o >= ox_last:
            cons_o = ox_last
            cons_f = cons_o / of
            self.end_burn = True
            self.burn_time = self.t[-1]
        # back to rates
        return cons_f / d_t, cons_o / d_t

    def _compute_chamber_pressure(
        self,
        d_t: float,
        m_dot_fuel: float,
        m_dot_ox: float,
    ) -> float:
        return rk4th_ode_solver(
            variables={"P0": self.P_0[-1]},
            equation=solve_pressure_fed_lre_chamber_pressure,
            d_t=d_t,
            R=self.motor.propellant.R_chamber,
            T0=self.motor.propellant.combustion_temperature,
            V0=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            At=self.motor.thrust_chamber.nozzle.get_throat_area(),
            k=self.motor.propellant.chamber_gamma,
            m_dot_ox=m_dot_ox,
            m_dot_fuel=m_dot_fuel,
        )[0]

    def _append_chamber_pressure(self, pressure: float) -> None:
        self.P_0 = np.append(self.P_0, pressure)

    def _compute_exit_pressure(self) -> float:
        return get_exit_pressure(
            self.motor.propellant.exit_gamma,
            self.motor.thrust_chamber.nozzle.expansion_ratio,
            self.P_0[-1],
        )

    def _append_exit_pressure(self, pressure: float) -> None:
        self.P_exit = np.append(self.P_exit, pressure)

    def _append_cf_correction(self, value: float) -> None:
        self.n_cf = np.append(self.n_cf, value)

    def _compute_thrust_coefficients(
        self,
        exit_pressure: float,
        P_ext: float,
    ) -> tuple[float, float]:
        return get_thrust_coefficients(
            self.P_0[-1],
            exit_pressure,
            P_ext,
            self.motor.thrust_chamber.nozzle.expansion_ratio,
            self.motor.propellant.exit_gamma,
            self.n_cf[-1],
        )

    def _append_thrust(self, cf: float, cf_ideal: float) -> None:
        thrust_val = get_thrust_from_cf(
            cf,
            self.P_0[-1],
            self.motor.thrust_chamber.nozzle.get_throat_area(),
        )
        self.C_f = np.append(self.C_f, cf)
        self.C_f_ideal = np.append(self.C_f_ideal, cf_ideal)
        self.thrust = np.append(self.thrust, thrust_val)

    def _update_propellant_masses(
        self, m_dot_fuel: float, m_dot_ox: float, d_t: float
    ) -> None:
        consumed_f = m_dot_fuel * d_t
        consumed_o = m_dot_ox * d_t

        self.motor.feed_system.fuel_tank.remove_propellant(consumed_f)
        self.motor.feed_system.oxidizer_tank.remove_propellant(consumed_o)

        new_fuel = self.fuel_mass[-1] - consumed_f
        new_ox = self.oxidizer_mass[-1] - consumed_o
        self.fuel_mass = np.append(self.fuel_mass, new_fuel)
        self.oxidizer_mass = np.append(self.oxidizer_mass, new_ox)
        self.m_prop = np.append(self.m_prop, new_fuel + new_ox)

    def _update_tank_pressures(self) -> None:
        new_fuel_tank_pressure = self.motor.feed_system.get_fuel_tank_pressure()
        new_oxidizer_tank_pressure = self.motor.feed_system.get_oxidizer_tank_pressure()

        self.fuel_tank_pressure = np.append(
            self.fuel_tank_pressure, new_fuel_tank_pressure
        )
        self.oxidizer_tank_pressure = np.append(
            self.oxidizer_tank_pressure, new_oxidizer_tank_pressure
        )

    def _check_burn_end(self) -> None:
        if self.end_burn:
            return
        if self.m_prop[-1] <= 0:
            self.end_burn = True
            self.burn_time = self.t[-1]

    def _check_thrust_end(self, P_ext: float) -> None:
        if not is_flow_choked(
            self.P_0[-1],
            P_ext,
            get_critical_pressure_ratio(self.motor.propellant.chamber_gamma),
        ):
            self._thrust_time = self.t[-1]
            self.end_thrust = True

    def print_results(self) -> None:
        """
        Prints the results obtained during the Liquid Rocket Engine operation.
        """
        # HEADER
        print("\nLIQUID ENGINE OPERATION RESULTS")

        # Propellant summary
        print(f"Initial propellant mass: {self.m_prop[0]:.4f} kg")
        try:
            print(f"Burnout time: {self.burn_time:.4f} s")
        except AttributeError:
            print("Burnout time: (not reached)")
        print(f"Thrust time: {self.thrust_time:.4f} s")

        # Chamber pressure
        print("\nCHAMBER PRESSURE (MPa)")
        print(f"  Max: {np.max(self.P_0) * 1e-6:.4f}")
        print(f"  Mean: {np.mean(self.P_0) * 1e-6:.4f}")

        # Thrust
        print("\nTHRUST (N)")
        print(f"  Max: {np.max(self.thrust):.4f}")
        print(f"  Mean: {np.mean(self.thrust):.4f}")

        # Impulse
        impulse = np.trapz(self.thrust, self.t)
        isp = impulse / (self.m_prop[0] * 9.81)
        print("\nIMPULSE AND I_SP")
        print(f"  Total impulse: {impulse:.4f} N·s")
        print(f"  Specific impulse: {isp:.4f} s")

        # Remaining propellant masses
        print("\nPROPELLANT REMAINING (kg)")
        print(f"  Oxidizer: {self.oxidizer_mass[-1]:.4f}")
        print(f"  Fuel:     {self.fuel_mass[-1]:.4f}")
