from __future__ import annotations

import machwave.core.compressible_flow.isentropic as isentropic
import machwave.core.compressible_flow.losses as losses
import machwave.core.compressible_flow.nozzle as nozzle_core
import machwave.core.conversions as conversions
import machwave.core.mass_balance as mass_balance
import machwave.core.solvers.rk4 as rk4
import machwave.models.motors as motors
import machwave.models.propellants.properties as propellant_properties_models
import machwave.simulation.biliquid.results as biliquid_results
import machwave.simulation.states as simulation_states


class BiliquidEngineState(simulation_states.MotorState):
    """State for a biliquid rocket engine."""

    motor: motors.BiliquidEngine
    result_class = biliquid_results.BiliquidSimulationResult

    def __init__(
        self,
        motor: motors.BiliquidEngine,
        igniter_pressure: float,
        external_pressure: float,
        other_losses: float,
    ) -> None:
        """
        Initialize a biliquid engine state.

        Args:
            motor: Biliquid engine to track.
            igniter_pressure: Initial chamber pressure from the igniter [Pa].
            external_pressure: Ambient pressure [Pa].
            other_losses: Fractional losses not covered by specific
                mechanisms, in [0, 1].
        """
        super().__init__(
            motor=motor,
            igniter_pressure=igniter_pressure,
            external_pressure=external_pressure,
            other_losses=other_losses,
        )

        self.oxidizer_mass: simulation_states.SimulationStateArray = [
            motor.feed_system.oxidizer_tank.initial_fluid_mass
        ]
        self.fuel_mass: simulation_states.SimulationStateArray = [
            motor.feed_system.fuel_tank.initial_fluid_mass
        ]

        self.fuel_mass_flow_rate: simulation_states.SimulationStateArray = []
        self.oxidizer_mass_flow_rate: simulation_states.SimulationStateArray = []
        self.oxidizer_to_fuel_ratio: simulation_states.SimulationStateArray = []
        self.fuel_tank_pressure: simulation_states.SimulationStateArray = []
        self.oxidizer_tank_pressure: simulation_states.SimulationStateArray = []
        self.nozzle_correction_factor: simulation_states.SimulationStateArray = []

    def get_m_dot_in(self) -> float:
        """Return the total inlet mass flow (fuel + oxidizer) [kg/s]."""
        return self.fuel_mass_flow_rate[-1] + self.oxidizer_mass_flow_rate[-1]

    def _evaluate_propellant_properties(
        self,
        chamber_pressure: float,
        mixture_ratio: float | None,
    ) -> propellant_properties_models.ThermochemicalProperties:
        """Evaluate the propellant at the chamber pressure and mixture ratio."""
        return self.motor.propellant.evaluate(
            chamber_pressure=chamber_pressure,
            expansion_ratio=self.motor.thrust_chamber.nozzle.expansion_ratio,
            mixture_ratio=mixture_ratio,
        )

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
        nozzle = self.motor.thrust_chamber.nozzle
        injector = self.motor.thrust_chamber.injector
        feed_system = self.motor.feed_system

        time = self.time[-1]
        chamber_pressure = self.chamber_pressure[-1]
        fuel_mass = self.fuel_mass[-1]
        oxidizer_mass = self.oxidizer_mass[-1]

        propellant_mass = fuel_mass + oxidizer_mass
        self.propellant_mass.append(propellant_mass)

        fuel_tank_pressure = feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass, fuel_mass=fuel_mass
        )
        self.fuel_tank_pressure.append(fuel_tank_pressure)
        oxidizer_tank_pressure = feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass
        )
        self.oxidizer_tank_pressure.append(oxidizer_tank_pressure)

        can_feed = (
            propellant_mass > 0
            and fuel_tank_pressure > chamber_pressure
            and oxidizer_tank_pressure > chamber_pressure
        )
        if can_feed:
            m_dot_fuel = feed_system.get_mass_flow_fuel(
                chamber_pressure=chamber_pressure,
                injector=injector,
                fuel_mass=fuel_mass,
                oxidizer_mass=oxidizer_mass,
            )
            m_dot_ox = feed_system.get_mass_flow_ox(
                chamber_pressure=chamber_pressure,
                injector=injector,
                oxidizer_mass=oxidizer_mass,
            )
        else:
            m_dot_fuel = m_dot_ox = 0.0

        m_dot_fuel = min(m_dot_fuel, fuel_mass / d_t)
        m_dot_ox = min(m_dot_ox, oxidizer_mass / d_t)
        self.fuel_mass_flow_rate.append(m_dot_fuel)
        self.oxidizer_mass_flow_rate.append(m_dot_ox)
        fuel_consumed = m_dot_fuel * d_t
        oxidizer_consumed = m_dot_ox * d_t

        if m_dot_fuel > 0.0:
            oxidizer_to_fuel_ratio = m_dot_ox / m_dot_fuel
        else:
            design_ratio = self.motor.propellant.oxidizer_to_fuel_ratio
            assert design_ratio is not None
            oxidizer_to_fuel_ratio = design_ratio
        self.oxidizer_to_fuel_ratio.append(oxidizer_to_fuel_ratio)

        propellant_properties = self._evaluate_propellant_properties(
            chamber_pressure=chamber_pressure,
            mixture_ratio=oxidizer_to_fuel_ratio,
        )

        exit_pressure = isentropic.get_exit_pressure(
            propellant_properties.k_exhaust,
            nozzle.expansion_ratio,
            chamber_pressure,
        )
        self.exit_pressure.append(exit_pressure)

        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
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
        nozzle_correction_factor = nozzle_efficiency * self.motor.combustion_efficiency
        self.nozzle_correction_factor.append(nozzle_correction_factor)

        ideal_thrust_coefficient = nozzle_core.get_ideal_thrust_coefficient(
            chamber_pressure,
            exit_pressure,
            external_pressure,
            nozzle.expansion_ratio,
            propellant_properties.k_exhaust,
        )
        self.ideal_thrust_coefficient.append(ideal_thrust_coefficient)
        thrust_coefficient = nozzle_core.apply_thrust_coefficient_correction(
            ideal_thrust_coefficient, nozzle_correction_factor
        )
        self.thrust_coefficient.append(thrust_coefficient)
        thrust = nozzle_core.get_thrust_from_thrust_coefficient(
            thrust_coefficient, chamber_pressure, nozzle.get_throat_area()
        )
        self.thrust.append(thrust)

        if (
            not can_feed
            or fuel_consumed >= fuel_mass
            or oxidizer_consumed >= oxidizer_mass
        ) and not self.end_burn:
            self.end_burn = True
            self._burn_time = time + d_t

        if not isentropic.is_flow_choked(
            chamber_pressure,
            external_pressure,
            isentropic.get_critical_pressure_ratio(propellant_properties.k_chamber),
        ):
            if self._burn_time is None:
                self._burn_time = time
            self._thrust_time = time
            self.end_thrust = True
            return

        new_time = time + d_t
        self.time.append(new_time)
        self.fuel_mass.append(fuel_mass - fuel_consumed)
        self.oxidizer_mass.append(oxidizer_mass - oxidizer_consumed)
        new_chamber_pressure = rk4.rk4th_ode_solver(
            variables={"chamber_pressure": chamber_pressure},
            equation=mass_balance.compute_chamber_pressure_mass_balance,
            d_t=d_t,
            external_pressure=external_pressure,
            mass_flow_in=self.get_m_dot_in(),
            free_chamber_volume=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            throat_area=nozzle.get_throat_area(),
            k=propellant_properties.k_chamber,
            R=propellant_properties.R_chamber,
            flame_temperature=propellant_properties.adiabatic_flame_temperature,
            nozzle_discharge_coefficient=nozzle.discharge_coefficient,
            free_chamber_volume_rate=0.0,
        )[0]
        self.chamber_pressure.append(new_chamber_pressure)
