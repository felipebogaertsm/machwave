import numpy as np

import machwave.core.conversions as conversions
import machwave.core.performance as performance
from machwave.core.compressible_flow.losses import (
    get_kinetics_loss_fraction,
    get_nozzle_divergent_loss_fraction,
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
    """

    motor: LiquidEngine

    SIMULATION_ARRAY_ATTRIBUTE_NAMES = MotorState.SIMULATION_ARRAY_ATTRIBUTE_NAMES + (
        "oxidizer_mass",
        "fuel_mass",
        "nozzle_correction_factor",
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
        self.nozzle_correction_factor: SimulationArray = [1.0]

        self.fuel_tank_pressure: SimulationArray = [
            motor.feed_system.get_fuel_tank_pressure()
        ]
        self.oxidizer_tank_pressure: SimulationArray = [
            motor.feed_system.get_oxidizer_tank_pressure()
        ]

    def get_m_dot_in(self) -> float:
        return self._m_dot_fuel + self._m_dot_ox

    def run_timestep(
        self,
        d_t: float,
        external_pressure: float,
    ) -> None:
        """
        Advance simulation by time step d_t under external pressure.

        Args:
            d_t: Time step.
            external_pressure: External pressure.
        """
        if self.end_thrust:
            return

        nz = self.motor.thrust_chamber.nozzle
        injector = self.motor.thrust_chamber.injector
        feed = self.motor.feed_system

        self.t.append(self.t[-1] + d_t)

        if self.propellant_mass[-1] > 0:
            m_dot_fuel = feed.get_mass_flow_fuel(
                chamber_pressure=self.chamber_pressure[-1],
                discharge_coefficient=injector.discharge_coefficient_fuel,
                injector_area=injector.area_fuel,
            )
            m_dot_ox = feed.get_mass_flow_ox(
                chamber_pressure=self.chamber_pressure[-1],
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
            chamber_pressure=self.chamber_pressure[-1],
            expansion_ratio=nz.expansion_ratio,
        )
        props = self.motor.propellant.properties
        assert props is not None

        new_chamber_pressure = rk4th_ode_solver(
            variables={"chamber_pressure": self.chamber_pressure[-1]},
            equation=compute_chamber_pressure_mass_balance,
            d_t=d_t,
            external_pressure=external_pressure,
            mass_flow_in=self.get_m_dot_in(),
            free_chamber_volume=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            throat_area=nz.get_throat_area(),
            k=props.k_chamber,
            R=props.R_chamber,
            flame_temperature=props.adiabatic_flame_temperature,
            discharge_coefficient=nz.discharge_coefficient,
        )[0]
        self.chamber_pressure.append(new_chamber_pressure)
        exit_pressure = get_exit_pressure(
            props.k_exhaust, nz.expansion_ratio, new_chamber_pressure
        )
        self.exit_pressure.append(exit_pressure)

        chamber_pressure_psi = conversions.convert_pa_to_psi(new_chamber_pressure)
        divergent_loss = get_nozzle_divergent_loss_fraction(
            divergent_angle=nz.divergent_angle,
        )
        kinetics_loss = get_kinetics_loss_fraction(
            i_sp_th_frozen=props.i_sp_frozen,
            i_sp_th_shifting=props.i_sp_shifting,
            chamber_pressure_psi=chamber_pressure_psi,
        )
        nozzle_efficiency = get_overall_nozzle_efficiency(
            divergent_loss, kinetics_loss, 0.0, 0.0, other_losses=self.other_losses
        )
        nozzle_correction_factor = (
            nozzle_efficiency * self.motor.propellant.combustion_efficiency
        )
        self.nozzle_correction_factor.append(nozzle_correction_factor)

        thrust_coefficient_ideal = get_ideal_thrust_coefficient(
            new_chamber_pressure,
            exit_pressure,
            external_pressure,
            nz.expansion_ratio,
            props.k_exhaust,
        )
        thrust_coefficient = apply_thrust_coefficient_correction(
            thrust_coefficient_ideal, nozzle_correction_factor
        )
        self.thrust_coefficient.append(thrust_coefficient)
        self.thrust_coefficient_ideal.append(thrust_coefficient_ideal)
        self.thrust.append(
            get_thrust_from_thrust_coefficient(
                thrust_coefficient, new_chamber_pressure, nz.get_throat_area()
            )
        )

        feed.fuel_tank.remove_propellant(cons_f)
        feed.oxidizer_tank.remove_propellant(cons_o)
        new_fuel = self.fuel_mass[-1] - cons_f
        new_ox = self.oxidizer_mass[-1] - cons_o
        self.fuel_mass.append(new_fuel)
        self.oxidizer_mass.append(new_ox)
        self.propellant_mass.append(new_fuel + new_ox)

        self.fuel_tank_pressure.append(feed.get_fuel_tank_pressure())
        self.oxidizer_tank_pressure.append(feed.get_oxidizer_tank_pressure())

        if self.propellant_mass[-1] <= 0 and not self.end_burn:
            self.end_burn = True
            self.burn_time = self.t[-1]
        if not is_flow_choked(
            new_chamber_pressure,
            external_pressure,
            get_critical_pressure_ratio(props.k_chamber),
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
        print(f"Initial propellant mass: {self.propellant_mass[0]:.4f} kg")
        try:
            print(f"Burnout time: {self.burn_time:.4f} s")
        except AttributeError:
            print("Burnout time: (not reached)")
        print(f"Thrust time: {self.thrust_time:.4f} s")

        # Chamber pressure
        print("\nCHAMBER PRESSURE (MPa)")
        print(f"  Max: {np.max(self.chamber_pressure) * 1e-6:.4f}")
        print(f"  Mean: {np.mean(self.chamber_pressure) * 1e-6:.4f}")

        # Thrust
        print("\nTHRUST (N)")
        print(f"  Max: {np.max(self.thrust):.4f}")
        print(f"  Mean: {np.mean(self.thrust):.4f}")

        # Impulse
        impulse = performance.get_total_impulse(
            np.asarray(self.thrust), np.asarray(self.t)
        )
        isp = performance.get_specific_impulse(impulse, self.propellant_mass[0])
        print("\nIMPULSE AND I_SP")
        print(f"  Total impulse: {impulse:.4f} N·s")
        print(f"  Specific impulse: {isp:.4f} s")

        # Remaining propellant masses
        print("\nPROPELLANT REMAINING (kg)")
        print(f"  Oxidizer: {self.oxidizer_mass[-1]:.4f}")
        print(f"  Fuel:     {self.fuel_mass[-1]:.4f}")
