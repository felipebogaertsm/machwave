from __future__ import annotations

import machwave.core.compressible_flow.isentropic as isentropic
import machwave.core.compressible_flow.losses as losses
import machwave.core.compressible_flow.nozzle as nozzle_core
import machwave.core.conversions as conversions
import machwave.core.mass_balance as mass_balance
import machwave.core.solvers.rk4 as rk4
import machwave.models.motors as motors
import machwave.simulation.states as simulation_states
from machwave.simulation.liquid.results import LiquidSimulationResult


class LiquidEngineState(simulation_states.MotorState):
    """State for a Liquid Rocket Engine."""

    motor: motors.LiquidEngine
    result_class = LiquidSimulationResult

    def __init__(
        self,
        motor: motors.LiquidEngine,
        igniter_pressure: float,
        external_pressure: float,
        other_losses: float,
    ) -> None:
        super().__init__(
            motor=motor,
            igniter_pressure=igniter_pressure,
            external_pressure=external_pressure,
            other_losses=other_losses,
        )

        self.oxidizer_mass: simulation_states.SimulationStateArray = [
            motor.feed_system.oxidizer_tank.fluid_mass
        ]
        self.fuel_mass: simulation_states.SimulationStateArray = [
            motor.feed_system.fuel_tank.fluid_mass
        ]
        self.nozzle_correction_factor: simulation_states.SimulationStateArray = [1.0]

        self.fuel_tank_pressure: simulation_states.SimulationStateArray = [
            motor.feed_system.get_fuel_tank_pressure()
        ]
        self.oxidizer_tank_pressure: simulation_states.SimulationStateArray = [
            motor.feed_system.get_oxidizer_tank_pressure()
        ]

    def get_m_dot_in(self) -> float:
        return self._m_dot_fuel + self._m_dot_ox

    def run_timestep(
        self,
        d_t: float,
        external_pressure: float,
    ) -> None:
        """Advance simulation by time step d_t under external pressure.

        Args:
            d_t: Time step.
            external_pressure: External pressure.
        """
        if self.end_thrust:
            return

        nozzle = self.motor.thrust_chamber.nozzle
        injector = self.motor.thrust_chamber.injector
        feed_system = self.motor.feed_system

        self.time.append(self.time[-1] + d_t)

        if self.propellant_mass[-1] > 0:
            m_dot_fuel = feed_system.get_mass_flow_fuel(
                chamber_pressure=self.chamber_pressure[-1],
                discharge_coefficient=injector.discharge_coefficient_fuel,
                injector_area=injector.area_fuel,
            )
            m_dot_ox = feed_system.get_mass_flow_ox(
                chamber_pressure=self.chamber_pressure[-1],
                discharge_coefficient=injector.discharge_coefficient_oxidizer,
                injector_area=injector.area_ox,
            )
        else:
            m_dot_fuel = m_dot_ox = 0.0

        m_dot_fuel = min(m_dot_fuel, self.fuel_mass[-1] / d_t)
        m_dot_ox = min(m_dot_ox, self.oxidizer_mass[-1] / d_t)

        oxidizer_to_fuel_ratio = self.motor.propellant.oxidizer_to_fuel_ratio
        assert oxidizer_to_fuel_ratio is not None
        fuel_consumed = m_dot_fuel * d_t
        oxidizer_consumed = m_dot_ox * d_t
        if (
            fuel_consumed >= self.fuel_mass[-1]
            or oxidizer_consumed >= self.oxidizer_mass[-1]
        ):
            self.end_burn = True
            self._burn_time = self.time[-1]
        self._m_dot_fuel = m_dot_fuel
        self._m_dot_ox = m_dot_ox

        if self.propellant_mass[-1] > 0:
            if m_dot_fuel > 0.0:
                instantaneous_oxidizer_to_fuel_ratio = m_dot_ox / m_dot_fuel
            else:
                instantaneous_oxidizer_to_fuel_ratio = oxidizer_to_fuel_ratio
            self.motor.propellant.properties = self.motor.propellant.evaluate(
                chamber_pressure=self.chamber_pressure[-1],
                expansion_ratio=nozzle.expansion_ratio,
                mixture_ratio=instantaneous_oxidizer_to_fuel_ratio,
            )
        propellant_properties = self.motor.propellant.properties
        assert propellant_properties is not None

        new_chamber_pressure = rk4.rk4th_ode_solver(
            variables={"chamber_pressure": self.chamber_pressure[-1]},
            equation=mass_balance.compute_chamber_pressure_mass_balance,
            d_t=d_t,
            external_pressure=external_pressure,
            mass_flow_in=self.get_m_dot_in(),
            free_chamber_volume=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            throat_area=nozzle.get_throat_area(),
            k=propellant_properties.k_chamber,
            R=propellant_properties.R_chamber,
            flame_temperature=propellant_properties.adiabatic_flame_temperature,
            discharge_coefficient=nozzle.discharge_coefficient,
        )[0]
        self.chamber_pressure.append(new_chamber_pressure)
        exit_pressure = isentropic.get_exit_pressure(
            propellant_properties.k_exhaust,
            nozzle.expansion_ratio,
            new_chamber_pressure,
        )
        self.exit_pressure.append(exit_pressure)

        chamber_pressure_psi = conversions.convert_pa_to_psi(new_chamber_pressure)
        divergent_loss = losses.get_nozzle_divergent_loss_fraction(
            divergent_angle=nozzle.divergent_angle,
        )
        kinetics_loss = losses.get_kinetics_loss_fraction(
            i_sp_th_frozen=propellant_properties.i_sp_frozen,
            i_sp_th_shifting=propellant_properties.i_sp_shifting,
            chamber_pressure_psi=chamber_pressure_psi,
        )
        nozzle_efficiency = losses.get_overall_nozzle_efficiency(
            divergent_loss, kinetics_loss, 0.0, 0.0, other_losses=self.other_losses
        )
        nozzle_correction_factor = (
            nozzle_efficiency * self.motor.propellant.combustion_efficiency
        )
        self.nozzle_correction_factor.append(nozzle_correction_factor)

        ideal_thrust_coefficient = nozzle_core.get_ideal_thrust_coefficient(
            new_chamber_pressure,
            exit_pressure,
            external_pressure,
            nozzle.expansion_ratio,
            propellant_properties.k_exhaust,
        )
        thrust_coefficient = nozzle_core.apply_thrust_coefficient_correction(
            ideal_thrust_coefficient, nozzle_correction_factor
        )
        self.thrust_coefficient.append(thrust_coefficient)
        self.ideal_thrust_coefficient.append(ideal_thrust_coefficient)
        self.thrust.append(
            nozzle_core.get_thrust_from_thrust_coefficient(
                thrust_coefficient, new_chamber_pressure, nozzle.get_throat_area()
            )
        )

        feed_system.fuel_tank.remove_propellant(fuel_consumed)
        feed_system.oxidizer_tank.remove_propellant(oxidizer_consumed)
        new_fuel = self.fuel_mass[-1] - fuel_consumed
        new_ox = self.oxidizer_mass[-1] - oxidizer_consumed
        self.fuel_mass.append(new_fuel)
        self.oxidizer_mass.append(new_ox)
        self.propellant_mass.append(new_fuel + new_ox)

        self.fuel_tank_pressure.append(feed_system.get_fuel_tank_pressure())
        self.oxidizer_tank_pressure.append(feed_system.get_oxidizer_tank_pressure())

        if self.propellant_mass[-1] <= 0 and not self.end_burn:
            self.end_burn = True
            self._burn_time = self.time[-1]
        if not isentropic.is_flow_choked(
            new_chamber_pressure,
            external_pressure,
            isentropic.get_critical_pressure_ratio(propellant_properties.k_chamber),
        ):
            if self._burn_time is None:
                self._burn_time = self.time[-1]
            self._thrust_time = self.time[-1]
            self.end_thrust = True
