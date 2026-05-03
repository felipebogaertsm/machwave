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
from machwave.states.base import MotorState, SimulationArray


class LiquidEngineState(MotorState):
    """
    State for a Liquid Rocket Engine.

    The variable names correspond to what they are commonly referred to in books and papers related to
    Rocket Propulsion. Therefore, PEP8's snake_case will not be followed rigorously.
    """

    motor: LiquidEngine

    SIMULATION_ARRAY_ATTRIBUTE_NAMES = MotorState.SIMULATION_ARRAY_ATTRIBUTE_NAMES + (
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

        self.oxidizer_mass: SimulationArray = [
            motor.feed_system.oxidizer_tank.fluid_mass
        ]
        self.fuel_mass: SimulationArray = [motor.feed_system.fuel_tank.fluid_mass]
        self.n_cf: SimulationArray = [1.0]

        self.fuel_tank_pressure: SimulationArray = [
            motor.feed_system.fuel_tank.get_pressure()
        ]
        self.oxidizer_tank_pressure: SimulationArray = [
            motor.feed_system.oxidizer_tank.get_pressure()
        ]

    def get_m_dot_in(self) -> float:
        return self._m_dot_fuel + self._m_dot_ox

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

        nz = self.motor.thrust_chamber.nozzle
        injector = self.motor.thrust_chamber.injector
        feed = self.motor.feed_system

        self.t.append(self.t[-1] + d_t)

        if self.m_prop[-1] > 0:
            m_dot_fuel = feed.get_mass_flow_fuel(
                chamber_pressure=self.P_0[-1],
                discharge_coefficient=injector.discharge_coefficient_fuel,
                injector_area=injector.area_fuel,
            )
            m_dot_ox = feed.get_mass_flow_ox(
                chamber_pressure=self.P_0[-1],
                discharge_coefficient=injector.discharge_coefficient_oxidizer,
                injector_area=injector.area_ox,
            )
        else:
            m_dot_fuel = m_dot_ox = 0.0

        m_dot_fuel = min(m_dot_fuel, self.fuel_mass[-1] / d_t)
        m_dot_ox = min(m_dot_ox, self.oxidizer_mass[-1] / d_t)

        of = self.motor.propellant.of_ratio
        assert of is not None
        cons_f = m_dot_fuel * d_t
        cons_o = m_dot_ox * d_t
        if cons_f >= self.fuel_mass[-1]:
            cons_f = self.fuel_mass[-1]
            cons_o = of * cons_f
            self.end_burn = True
            self.burn_time = self.t[-1]
        elif cons_o >= self.oxidizer_mass[-1]:
            cons_o = self.oxidizer_mass[-1]
            cons_f = cons_o / of
            self.end_burn = True
            self.burn_time = self.t[-1]
        m_dot_fuel = cons_f / d_t
        m_dot_ox = cons_o / d_t
        self._m_dot_fuel = m_dot_fuel
        self._m_dot_ox = m_dot_ox

        self.motor.propellant.properties = self.motor.propellant.evaluate(
            chamber_pressure=self.P_0[-1],
            expansion_ratio=nz.expansion_ratio,
        )
        props = self.motor.propellant.properties
        assert props is not None

        new_P = rk4th_ode_solver(
            variables={"P0": self.P_0[-1]},
            equation=compute_chamber_pressure_mass_balance,
            d_t=d_t,
            Pe=P_ext,
            m_in=self.get_m_dot_in(),
            V0=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            At=nz.get_throat_area(),
            k=props.gamma_chamber,
            R=props.R_chamber,
            T0=props.adiabatic_flame_temperature,
        )[0]
        self.P_0.append(new_P)
        P_exit = get_exit_pressure(props.gamma_exhaust, nz.expansion_ratio, new_P)
        self.P_exit.append(P_exit)

        chamber_pressure_psi = conversions.convert_pa_to_psi(new_P)
        eta_div = get_nozzle_divergent_percentage_loss(
            divergent_angle=nz.divergent_angle,
        )
        eta_kin = get_kinetics_percentage_loss(
            i_sp_th_frozen=props.i_sp_frozen,
            i_sp_th_shifting=props.i_sp_shifting,
            chamber_pressure_psi=chamber_pressure_psi,
        )
        nozzle_efficiency = get_overall_nozzle_efficiency(
            eta_div, eta_kin, 0.0, 0.0, other_losses=self.other_losses
        )
        n_cf = nozzle_efficiency * self.motor.propellant.combustion_efficiency
        self.n_cf.append(n_cf)

        cf_ideal = get_ideal_thrust_coefficient(
            new_P,
            P_exit,
            P_ext,
            nz.expansion_ratio,
            props.gamma_exhaust,
        )
        cf = apply_thrust_coefficient_correction(cf_ideal, n_cf)
        self.C_f.append(cf)
        self.C_f_ideal.append(cf_ideal)
        self.thrust.append(
            get_thrust_from_thrust_coefficient(cf, new_P, nz.get_throat_area())
        )

        feed.fuel_tank.remove_propellant(cons_f)
        feed.oxidizer_tank.remove_propellant(cons_o)
        new_fuel = self.fuel_mass[-1] - cons_f
        new_ox = self.oxidizer_mass[-1] - cons_o
        self.fuel_mass.append(new_fuel)
        self.oxidizer_mass.append(new_ox)
        self.m_prop.append(new_fuel + new_ox)

        self.fuel_tank_pressure.append(feed.get_fuel_tank_pressure())
        self.oxidizer_tank_pressure.append(feed.get_oxidizer_tank_pressure())

        if self.m_prop[-1] <= 0 and not self.end_burn:
            self.end_burn = True
            self.burn_time = self.t[-1]
        if not is_flow_choked(
            new_P,
            P_ext,
            get_critical_pressure_ratio(props.gamma_chamber),
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
