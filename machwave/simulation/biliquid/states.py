from __future__ import annotations

import functools
from typing import Callable

import machwave.core.compressible_flow.isentropic as isentropic
import machwave.core.compressible_flow.nozzle as nozzle_core
import machwave.core.mass_balance as mass_balance
import machwave.core.performance as performance
import machwave.core.solvers.rk4 as rk4
import machwave.models.feed_systems as feed_systems
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.motors as motors
import machwave.models.propellants.properties as propellant_properties_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.simulation.biliquid.results as biliquid_results
import machwave.simulation.states as simulation_states


def get_injector_mass_flows(
    chamber_pressure: float,
    *,
    feed_system: feed_systems.FeedSystem,
    injector: injector_models.BipropellantInjector,
    fuel_mass: float,
    oxidizer_mass: float,
    fuel_tank_pressure: float,
    oxidizer_tank_pressure: float,
    is_feeding: bool,
    d_t: float,
) -> tuple[float, float]:
    """Fuel and oxidizer injector flows at the given chamber pressure [kg/s]."""
    if not is_feeding:
        return 0.0, 0.0
    fuel_flow = (
        feed_system.get_mass_flow_fuel(
            chamber_pressure=chamber_pressure,
            injector=injector,
            fuel_mass=fuel_mass,
            oxidizer_mass=oxidizer_mass,
        )
        if fuel_tank_pressure > chamber_pressure
        else 0.0
    )
    oxidizer_flow = (
        feed_system.get_mass_flow_ox(
            chamber_pressure=chamber_pressure,
            injector=injector,
            oxidizer_mass=oxidizer_mass,
        )
        if oxidizer_tank_pressure > chamber_pressure
        else 0.0
    )
    return (
        min(fuel_flow, fuel_mass / d_t),
        min(oxidizer_flow, oxidizer_mass / d_t),
    )


def get_total_injector_mass_flow(
    chamber_pressure: float,
    *,
    injector_flows: Callable[[float], tuple[float, float]],
) -> float:
    """Total injector mass flow (fuel + oxidizer) at the given pressure [kg/s]."""
    return sum(injector_flows(chamber_pressure))


class BiliquidEngineState(simulation_states.MotorState):
    """State for a biliquid rocket engine."""

    motor: motors.BiliquidEngine
    result_class = biliquid_results.BiliquidSimulationResult

    def __init__(
        self,
        motor: motors.BiliquidEngine,
        igniter_pressure: float,
        external_pressure: float,
    ) -> None:
        """
        Initialize a biliquid engine state.

        Args:
            motor: Biliquid engine to track.
            igniter_pressure: Initial chamber pressure from the igniter [Pa].
            external_pressure: Ambient pressure [Pa].
        """
        super().__init__(
            motor=motor,
            igniter_pressure=igniter_pressure,
            external_pressure=external_pressure,
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

        is_feeding = (
            propellant_mass > 0
            and fuel_tank_pressure > chamber_pressure
            and oxidizer_tank_pressure > chamber_pressure
        )
        injector_flows = functools.partial(
            get_injector_mass_flows,
            feed_system=feed_system,
            injector=self.motor.thrust_chamber.injector,
            fuel_mass=fuel_mass,
            oxidizer_mass=oxidizer_mass,
            fuel_tank_pressure=fuel_tank_pressure,
            oxidizer_tank_pressure=oxidizer_tank_pressure,
            is_feeding=is_feeding,
            d_t=d_t,
        )
        m_dot_fuel, m_dot_ox = injector_flows(chamber_pressure)
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

        effective_expansion_ratio, exit_pressure = (
            nozzle_core.get_separated_exit_conditions(
                propellant_properties.k_exhaust,
                nozzle.expansion_ratio,
                chamber_pressure,
                external_pressure,
                nozzle.separation_pressure_ratio,
            )
        )
        self.exit_pressure.append(exit_pressure)

        momentum_term, pressure_term = (
            nozzle_core.get_ideal_thrust_coefficient_components(
                chamber_pressure,
                exit_pressure,
                external_pressure,
                effective_expansion_ratio,
                propellant_properties.k_exhaust,
            )
        )
        self.ideal_thrust_coefficient.append(momentum_term + pressure_term)

        loss_context = nozzle_losses.NozzleLossEvaluationContext(
            time=time,
            chamber_pressure=chamber_pressure,
            nozzle=nozzle,
            propellant_properties=propellant_properties,
            free_chamber_volume=(
                self.motor.thrust_chamber.combustion_chamber.internal_volume
            ),
        )
        loss_result = self.motor.nozzle_loss_model.evaluate(
            momentum_term, pressure_term, loss_context
        )
        self.nozzle_efficiency.append(loss_result.nozzle_efficiency)
        for name, fraction in loss_result.fractions.items():
            self.loss_fractions[name].append(fraction)

        thrust_coefficient = loss_result.momentum_term + loss_result.pressure_term
        self.thrust_coefficient.append(thrust_coefficient)
        thrust = nozzle_core.get_thrust_from_thrust_coefficient(
            thrust_coefficient, chamber_pressure, nozzle.get_throat_area()
        )
        self.thrust.append(thrust)

        if (
            not is_feeding
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
        effective_flame_temperature = performance.get_effective_flame_temperature(
            adiabatic_flame_temperature=propellant_properties.adiabatic_flame_temperature,
            combustion_efficiency=self.motor.combustion_efficiency,
        )
        new_chamber_pressure = rk4.rk4th_ode_solver(
            variables={"chamber_pressure": chamber_pressure},
            equation=mass_balance.compute_chamber_pressure_mass_balance,
            d_t=d_t,
            external_pressure=external_pressure,
            mass_flow_in=functools.partial(
                get_total_injector_mass_flow, injector_flows=injector_flows
            ),
            free_chamber_volume=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            throat_area=nozzle.get_throat_area(),
            k=propellant_properties.k_chamber,
            R=propellant_properties.R_chamber,
            flame_temperature=effective_flame_temperature,
            nozzle_discharge_coefficient=nozzle.discharge_coefficient,
        )[0]
        self.chamber_pressure.append(new_chamber_pressure)
        self.fuel_mass.append(fuel_mass - fuel_consumed)
        self.oxidizer_mass.append(oxidizer_mass - oxidizer_consumed)
