from __future__ import annotations

import dataclasses
import functools
import math
from typing import Callable

import machwave.common.fluid_state as fluid_state_models
import machwave.core.mass_balance as mass_balance
import machwave.core.performance as performance
import machwave.core.solvers.rk4 as rk4
import machwave.models.feed_systems.tank as tank_models
import machwave.models.motors as motors
import machwave.models.propellants.properties as propellant_properties_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.simulation.biliquid.results as biliquid_results
import machwave.simulation.states as simulation_states


def get_injector_mass_flows(
    chamber_pressure: float,
    *,
    injector: injector_models.BipropellantInjector,
    fuel_inlet: fluid_state_models.FluidState,
    oxidizer_inlet: fluid_state_models.FluidState,
    fuel_mass: float,
    oxidizer_mass: float,
    is_feeding: bool,
    d_t: float,
) -> tuple[float, float]:
    """Fuel and oxidizer injector flows at the given chamber pressure [kg/s]."""
    if not is_feeding:
        return 0.0, 0.0
    fuel_flow = (
        injector.get_mass_flow_fuel(
            inlet=fuel_inlet,
            chamber_pressure=chamber_pressure,
        )
        if fuel_inlet.pressure > chamber_pressure
        else 0.0
    )
    oxidizer_flow = (
        injector.get_mass_flow_ox(
            inlet=oxidizer_inlet,
            chamber_pressure=chamber_pressure,
        )
        if oxidizer_inlet.pressure > chamber_pressure
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


@dataclasses.dataclass(frozen=True, kw_only=True)
class BiliquidTimestepConditions(simulation_states.TimestepConditions):
    """Timestep conditions for a biliquid engine."""

    fuel_mass: float
    oxidizer_mass: float
    fuel_mass_flow_rate: float
    oxidizer_mass_flow_rate: float
    oxidizer_to_fuel_ratio: float
    fuel_tank_pressure: float
    oxidizer_tank_pressure: float
    fuel_tank_temperature: float
    oxidizer_tank_temperature: float


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

        oxidizer_tank = motor.feed_system.oxidizer_tank
        fuel_tank = motor.feed_system.fuel_tank

        self.oxidizer_mass: simulation_states.SimulationStateArray = [
            oxidizer_tank.initial_fluid_mass
        ]
        self.fuel_mass: simulation_states.SimulationStateArray = [
            fuel_tank.initial_fluid_mass
        ]

        # Second state variable of a tank running an energy balance, which the
        # integrator carries beside the mass. An isothermal tank has none.
        self.oxidizer_internal_energy: float | None = (
            None if oxidizer_tank.isothermal else oxidizer_tank.initial_internal_energy
        )
        self.fuel_internal_energy: float | None = (
            None if fuel_tank.isothermal else fuel_tank.initial_internal_energy
        )

        self.fuel_mass_flow_rate: simulation_states.SimulationStateArray = []
        self.oxidizer_mass_flow_rate: simulation_states.SimulationStateArray = []
        self.oxidizer_to_fuel_ratio: simulation_states.SimulationStateArray = []
        self.fuel_tank_pressure: simulation_states.SimulationStateArray = []
        self.oxidizer_tank_pressure: simulation_states.SimulationStateArray = []
        self.fuel_tank_temperature: simulation_states.SimulationStateArray = []
        self.oxidizer_tank_temperature: simulation_states.SimulationStateArray = []

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
        Iterate the engine operation by calculating operational parameters.

        Args:
            d_t: Time increment [s].
            external_pressure: External pressure [Pa].
        """
        nozzle = self.motor.thrust_chamber.nozzle
        feed_system = self.motor.feed_system

        time = self.time[-1]
        chamber_pressure = self.chamber_pressure[-1]
        fuel_mass = self.fuel_mass[-1]
        oxidizer_mass = self.oxidizer_mass[-1]
        fuel_internal_energy = self.fuel_internal_energy
        oxidizer_internal_energy = self.oxidizer_internal_energy

        propellant_mass = fuel_mass + oxidizer_mass
        self.propellant_mass.append(propellant_mass)

        fuel_inlet = feed_system.get_fuel_inlet_state(
            oxidizer_mass=oxidizer_mass,
            fuel_mass=fuel_mass,
            fuel_internal_energy=fuel_internal_energy,
            oxidizer_internal_energy=oxidizer_internal_energy,
        )
        oxidizer_inlet = feed_system.get_oxidizer_inlet_state(
            oxidizer_mass=oxidizer_mass,
            oxidizer_internal_energy=oxidizer_internal_energy,
        )

        fuel_tank_pressure = feed_system.get_fuel_tank_pressure(
            oxidizer_mass=oxidizer_mass,
            fuel_mass=fuel_mass,
            fuel_internal_energy=fuel_internal_energy,
            oxidizer_internal_energy=oxidizer_internal_energy,
        )
        self.fuel_tank_pressure.append(fuel_tank_pressure)
        oxidizer_tank_pressure = feed_system.get_oxidizer_tank_pressure(
            oxidizer_mass=oxidizer_mass,
            oxidizer_internal_energy=oxidizer_internal_energy,
        )
        self.oxidizer_tank_pressure.append(oxidizer_tank_pressure)

        fuel_tank_temperature = feed_system.fuel_tank.get_temperature(
            fuel_mass, fuel_internal_energy
        )
        self.fuel_tank_temperature.append(fuel_tank_temperature)
        oxidizer_tank_temperature = feed_system.oxidizer_tank.get_temperature(
            oxidizer_mass, oxidizer_internal_energy
        )
        self.oxidizer_tank_temperature.append(oxidizer_tank_temperature)

        is_feeding = (
            not self.end_burn
            and fuel_mass > 0
            and oxidizer_mass > 0
            and fuel_tank_pressure > chamber_pressure
            and oxidizer_tank_pressure > chamber_pressure
        )
        injector_flows = functools.partial(
            get_injector_mass_flows,
            injector=self.motor.thrust_chamber.injector,
            fuel_inlet=fuel_inlet,
            oxidizer_inlet=oxidizer_inlet,
            fuel_mass=fuel_mass,
            oxidizer_mass=oxidizer_mass,
            is_feeding=is_feeding,
            d_t=d_t,
        )
        m_dot_fuel, m_dot_ox = injector_flows(chamber_pressure)
        self.fuel_mass_flow_rate.append(m_dot_fuel)
        self.oxidizer_mass_flow_rate.append(m_dot_ox)
        fuel_consumed = m_dot_fuel * d_t
        oxidizer_consumed = m_dot_ox * d_t

        # Without both flows strictly positive, the OF ratio is NaN
        mixture_ratio = (
            m_dot_ox / m_dot_fuel if m_dot_fuel > 0.0 and m_dot_ox > 0.0 else None
        )
        oxidizer_to_fuel_ratio = math.nan if mixture_ratio is None else mixture_ratio
        self.oxidizer_to_fuel_ratio.append(oxidizer_to_fuel_ratio)

        propellant_properties = self._evaluate_propellant_properties(
            chamber_pressure=chamber_pressure,
            mixture_ratio=mixture_ratio,
        )

        (
            effective_expansion_ratio,
            exit_pressure,
            ideal_momentum_term,
            ideal_pressure_term,
        ) = self._ideal_thrust_coefficient_terms(
            propellant_properties.k_exhaust, chamber_pressure, external_pressure
        )

        timestep_conditions = BiliquidTimestepConditions(
            time=time,
            chamber_pressure=chamber_pressure,
            external_pressure=external_pressure,
            exit_pressure=exit_pressure,
            effective_expansion_ratio=effective_expansion_ratio,
            free_chamber_volume=(
                self.motor.thrust_chamber.combustion_chamber.internal_volume
            ),
            propellant_mass=propellant_mass,
            propellant_mass_flow_rate=m_dot_fuel + m_dot_ox,
            nozzle=nozzle,
            propellant_properties=propellant_properties,
            fuel_mass=fuel_mass,
            oxidizer_mass=oxidizer_mass,
            fuel_mass_flow_rate=m_dot_fuel,
            oxidizer_mass_flow_rate=m_dot_ox,
            oxidizer_to_fuel_ratio=oxidizer_to_fuel_ratio,
            fuel_tank_pressure=fuel_tank_pressure,
            oxidizer_tank_pressure=oxidizer_tank_pressure,
            fuel_tank_temperature=fuel_tank_temperature,
            oxidizer_tank_temperature=oxidizer_tank_temperature,
        )
        self._apply_nozzle_losses(
            ideal_momentum_term,
            ideal_pressure_term,
            timestep_conditions,
            chamber_pressure,
        )

        if (
            not is_feeding
            or fuel_consumed >= fuel_mass
            or oxidizer_consumed >= oxidizer_mass
        ) and not self.end_burn:
            self.end_burn = True
            self._burn_time = time + d_t

        if self._update_thrust_termination(
            time,
            chamber_pressure,
            external_pressure,
            propellant_properties.k_chamber,
        ):
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

        self.fuel_internal_energy = self._drain_internal_energy(
            tank=feed_system.fuel_tank,
            internal_energy=fuel_internal_energy,
            fluid_mass=fuel_mass,
            mass_drained=fuel_consumed,
        )
        self.oxidizer_internal_energy = self._drain_internal_energy(
            tank=feed_system.oxidizer_tank,
            internal_energy=oxidizer_internal_energy,
            fluid_mass=oxidizer_mass,
            mass_drained=oxidizer_consumed,
        )

    @staticmethod
    def _drain_internal_energy(
        *,
        tank: tank_models.Tank,
        internal_energy: float | None,
        fluid_mass: float,
        mass_drained: float,
    ) -> float | None:
        """
        Take the enthalpy the drained fluid carries out of the tank [J].

        The tank is adiabatic and does no work on anything but the fluid it
        pushes out, so its internal energy falls by the enthalpy of what left.
        The fluid behind boils to refill the ullage and cools doing it, which
        is what walks the saturation pressure down over the burn.

        Returns:
            The internal energy left in the tank [J], or None for an
            isothermal tank, which runs no energy balance.
        """
        if internal_energy is None or mass_drained <= 0.0:
            return internal_energy

        return internal_energy - mass_drained * tank.get_outflow_specific_enthalpy(
            fluid_mass, internal_energy
        )
