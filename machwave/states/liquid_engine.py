import numpy as np
import scipy.constants

import machwave.core.conversions as conversions
from machwave.core.compressible_flow.losses import (
    get_kinetics_percentage_loss,
    get_nozzle_divergent_percentage_loss,
    get_overall_nozzle_efficiency,
)
from machwave.core.compressible_flow.nozzle import (
    apply_thrust_coefficient_correction,
    get_ideal_thrust_coefficient,
    get_thrust_from_thrust_coefficient,
)
from machwave.core.compressible_flow.isentropic import (
    get_critical_pressure_ratio,
    get_exit_pressure,
    is_flow_choked,
)
from machwave.core.mass_balance import compute_chamber_pressure_mass_balance
from machwave.core.solvers import rk4th_ode_solver
from machwave.models.motors import LiquidEngine
from machwave.states.base import MotorState


class LiquidEngineState(MotorState):
    """
    State for a Liquid Rocket Engine.

    The variable names correspond to what they are commonly referred to in books and papers related to
    Rocket Propulsion. Therefore, PEP8's snake_case will not be followed rigorously.
    """

    motor: LiquidEngine

    _ARRAY_ATTRS = MotorState._ARRAY_ATTRS + (
        "oxidizer_mass",
        "fuel_mass",
        "n_cf",
        "fuel_tank_pressure",
        "oxidizer_tank_pressure",
    )

    def __init__(
        self,
        motor: LiquidEngine,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
        other_losses: float,
    ) -> None:
        """
        Initial parameters for a LRE operation.
        """
        super().__init__(
            motor=motor,
            initial_pressure=initial_pressure,
            initial_atmospheric_pressure=initial_atmospheric_pressure,
            other_losses=other_losses,
        )

        self.oxidizer_mass: list[float] = [motor.feed_system.oxidizer_tank.fluid_mass]
        self.fuel_mass: list[float] = [motor.feed_system.fuel_tank.fluid_mass]
        self.n_cf: list[float] = [1.0]

        self.fuel_tank_pressure: list[float] = [
            motor.feed_system.fuel_tank.get_pressure()
        ]
        self.oxidizer_tank_pressure: list[float] = [
            motor.feed_system.oxidizer_tank.get_pressure()
        ]

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
        self._m_dot_fuel = m_dot_fuel
        self._m_dot_ox = m_dot_ox
        self._update_propellant_properties()

        new_P = self._compute_chamber_pressure(d_t, P_ext)
        self._append_chamber_pressure(new_P)
        P_exit = self._compute_exit_pressure()
        self._append_exit_pressure(P_exit)
        n_cf = self._compute_cf_correction()
        self._append_cf_correction(n_cf)
        cf, cf_ideal = self._compute_thrust_coefficients(P_exit, P_ext)
        self._append_thrust(cf, cf_ideal)

        self._update_propellant_masses(m_dot_fuel, m_dot_ox, d_t)
        self._update_tank_pressures()
        self._check_burn_end()
        self._check_thrust_end(P_ext)

    def _append_time(self, d_t: float) -> None:
        self.t.append(self.t[-1] + d_t)

    def _update_propellant_properties(self) -> None:
        self.motor.propellant.properties = self.motor.propellant.evaluate(
            chamber_pressure=self.P_0[-1],
            expansion_ratio=self.motor.thrust_chamber.nozzle.expansion_ratio,
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
        assert of is not None
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

    def get_m_dot_in(self) -> float:
        return self._m_dot_fuel + self._m_dot_ox

    def _compute_chamber_pressure(self, d_t: float, P_ext: float) -> float:
        props = self.motor.propellant.properties
        assert props is not None
        return rk4th_ode_solver(
            variables={"P0": self.P_0[-1]},
            equation=compute_chamber_pressure_mass_balance,
            d_t=d_t,
            Pe=P_ext,
            m_in=self.get_m_dot_in(),
            V0=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            At=self.motor.thrust_chamber.nozzle.get_throat_area(),
            k=props.gamma_chamber,
            R=props.R_chamber,
            T0=props.adiabatic_flame_temperature,
        )[0]

    def _append_chamber_pressure(self, pressure: float) -> None:
        self.P_0.append(pressure)

    def _compute_exit_pressure(self) -> float:
        assert self.motor.propellant.properties is not None
        return get_exit_pressure(
            self.motor.propellant.properties.gamma_exhaust,
            self.motor.thrust_chamber.nozzle.expansion_ratio,
            self.P_0[-1],
        )

    def _append_exit_pressure(self, pressure: float) -> None:
        self.P_exit.append(pressure)

    def _compute_cf_correction(self) -> float:
        """Compute the overall thrust coefficient correction factor.

        Applies divergent nozzle loss, kinetics loss (frozen vs shifting Isp), and
        combustion efficiency. Boundary layer and two-phase losses are omitted for
        liquid propellants (gas-only combustion, no condensed phase).

        Returns:
            Overall nozzle correction factor (0–1).
        """
        assert self.motor.propellant.properties is not None
        props = self.motor.propellant.properties
        nozzle = self.motor.thrust_chamber.nozzle
        chamber_pressure_psi = conversions.convert_pa_to_psi(self.P_0[-1])

        eta_div = get_nozzle_divergent_percentage_loss(
            divergent_angle=nozzle.divergent_angle,
        )
        eta_kin = get_kinetics_percentage_loss(
            i_sp_th_frozen=props.i_sp_frozen,
            i_sp_th_shifting=props.i_sp_shifting,
            chamber_pressure_psi=chamber_pressure_psi,
        )
        nozzle_efficiency = get_overall_nozzle_efficiency(
            eta_div, eta_kin, 0.0, 0.0, other_losses=self.other_losses
        )
        return nozzle_efficiency * self.motor.propellant.combustion_efficiency

    def _append_cf_correction(self, value: float) -> None:
        self.n_cf.append(value)

    def _compute_thrust_coefficients(
        self,
        exit_pressure: float,
        P_ext: float,
    ) -> tuple[float, float]:
        assert self.motor.propellant.properties is not None
        cf_ideal = get_ideal_thrust_coefficient(
            self.P_0[-1],
            exit_pressure,
            P_ext,
            self.motor.thrust_chamber.nozzle.expansion_ratio,
            self.motor.propellant.properties.gamma_exhaust,
        )
        cf = apply_thrust_coefficient_correction(cf_ideal, self.n_cf[-1])
        return cf, cf_ideal

    def _append_thrust(self, cf: float, cf_ideal: float) -> None:
        thrust_val = get_thrust_from_thrust_coefficient(
            cf,
            self.P_0[-1],
            self.motor.thrust_chamber.nozzle.get_throat_area(),
        )
        self.C_f.append(cf)
        self.C_f_ideal.append(cf_ideal)
        self.thrust.append(thrust_val)

    def _update_propellant_masses(
        self, m_dot_fuel: float, m_dot_ox: float, d_t: float
    ) -> None:
        consumed_f = m_dot_fuel * d_t
        consumed_o = m_dot_ox * d_t

        self.motor.feed_system.fuel_tank.remove_propellant(consumed_f)
        self.motor.feed_system.oxidizer_tank.remove_propellant(consumed_o)

        new_fuel = self.fuel_mass[-1] - consumed_f
        new_ox = self.oxidizer_mass[-1] - consumed_o
        self.fuel_mass.append(new_fuel)
        self.oxidizer_mass.append(new_ox)
        self.m_prop.append(new_fuel + new_ox)

    def _update_tank_pressures(self) -> None:
        new_fuel_tank_pressure = self.motor.feed_system.get_fuel_tank_pressure()
        new_oxidizer_tank_pressure = self.motor.feed_system.get_oxidizer_tank_pressure()

        self.fuel_tank_pressure.append(new_fuel_tank_pressure)
        self.oxidizer_tank_pressure.append(new_oxidizer_tank_pressure)

    def _check_burn_end(self) -> None:
        if self.end_burn:
            return
        if self.m_prop[-1] <= 0:
            self.end_burn = True
            self.burn_time = self.t[-1]

    def _check_thrust_end(self, P_ext: float) -> None:
        assert self.motor.propellant.properties is not None
        if not is_flow_choked(
            self.P_0[-1],
            P_ext,
            get_critical_pressure_ratio(self.motor.propellant.properties.gamma_chamber),
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
        impulse = np.trapezoid(self.thrust, self.t)
        isp = impulse / (self.m_prop[0] * scipy.constants.g)
        print("\nIMPULSE AND I_SP")
        print(f"  Total impulse: {impulse:.4f} N·s")
        print(f"  Specific impulse: {isp:.4f} s")

        # Remaining propellant masses
        print("\nPROPELLANT REMAINING (kg)")
        print(f"  Oxidizer: {self.oxidizer_mass[-1]:.4f}")
        print(f"  Fuel:     {self.fuel_mass[-1]:.4f}")
