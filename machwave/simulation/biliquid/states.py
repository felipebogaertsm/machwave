from __future__ import annotations

import dataclasses
import functools
import math
from collections.abc import Mapping
from typing import Callable

import machwave.common.fluid_state as fluid_state_models
import machwave.core.mass_balance as mass_balance
import machwave.core.performance as performance
import machwave.core.solvers.rk4 as rk4
import machwave.models.feed_systems.lines as line_models
import machwave.models.feed_systems.tank as tank_models
import machwave.models.motors as motors
import machwave.models.propellants.components as propellant_components
import machwave.models.propellants.properties as propellant_properties_models
import machwave.models.thrust_chamber.injector as injector_models
import machwave.simulation.biliquid.results as biliquid_results
import machwave.simulation.states as simulation_states


def get_injector_mass_flows(
    chamber_pressure: float,
    *,
    injector: injector_models.Injector,
    inlet_states: Mapping[str, fluid_state_models.FluidState],
    line_masses: Mapping[str, float],
    is_feeding: bool,
    d_t: float,
) -> dict[str, float]:
    """
    Injector flow on every line at the given chamber pressure [kg/s].

    No line delivers more than the mass it has left over the timestep.
    """
    if not is_feeding:
        return {name: 0.0 for name in inlet_states}

    flows = injector.get_mass_flows(
        inlet_states=inlet_states, chamber_pressure=chamber_pressure
    )
    return {name: min(flow, line_masses[name] / d_t) for name, flow in flows.items()}


def get_total_injector_mass_flow(
    chamber_pressure: float,
    *,
    injector_flows: Callable[[float], Mapping[str, float]],
) -> float:
    """Total injector mass flow over every line at the given pressure [kg/s]."""
    return sum(injector_flows(chamber_pressure).values())


@dataclasses.dataclass(frozen=True, kw_only=True)
class BiliquidTimestepConditions(simulation_states.TimestepConditions):
    """Timestep conditions for a biliquid engine."""

    fluid_mass_per_line: dict[str, float]
    mass_flow_rate_per_line: dict[str, float]
    oxidizer_to_fuel_ratio: float
    tank_pressure_per_line: dict[str, float]
    tank_temperature_per_line: dict[str, float]


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

        feed_system = motor.feed_system
        self.lines: dict[str, line_models.PropellantLine] = feed_system.lines
        self.oxidizer_line_names = tuple(
            line.name
            for line in feed_system.get_lines_with_role(
                propellant_components.ComponentRole.OXIDIZER
            )
        )
        self.fuel_line_names = tuple(
            line.name
            for line in feed_system.get_lines_with_role(
                propellant_components.ComponentRole.FUEL
            )
        )

        initial_states = {name: line.initial_state for name, line in self.lines.items()}
        self.fluid_mass_per_line: dict[str, simulation_states.SimulationStateArray] = {
            name: [state.fluid_mass] for name, state in initial_states.items()
        }

        # Second state variable of a tank running an energy balance, which the
        # integrator carries beside the mass. An isothermal tank has none.
        self.internal_energy_per_line: dict[str, float | None] = {
            name: state.internal_energy for name, state in initial_states.items()
        }

        self.mass_flow_rate_per_line: dict[
            str, simulation_states.SimulationStateArray
        ] = {name: [] for name in self.lines}
        self.tank_pressure_per_line: dict[
            str, simulation_states.SimulationStateArray
        ] = {name: [] for name in self.lines}
        self.tank_temperature_per_line: dict[
            str, simulation_states.SimulationStateArray
        ] = {name: [] for name in self.lines}
        self.oxidizer_to_fuel_ratio: simulation_states.SimulationStateArray = []

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

    def _get_mixture_ratio(self, mass_flows: Mapping[str, float]) -> float | None:
        """
        Total oxidizer flow over total fuel flow.

        None where the ratio has no meaning: a monoliquid, or an engine whose
        lines have stopped flowing.
        """
        oxidizer_flow = sum(mass_flows[name] for name in self.oxidizer_line_names)
        fuel_flow = sum(mass_flows[name] for name in self.fuel_line_names)

        if oxidizer_flow <= 0.0 or fuel_flow <= 0.0:
            return None

        return oxidizer_flow / fuel_flow

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
        fluid_masses = {
            name: series[-1] for name, series in self.fluid_mass_per_line.items()
        }

        propellant_mass = sum(fluid_masses.values())
        self.propellant_mass.append(propellant_mass)

        inlet_states = feed_system.get_inlet_states(
            {
                name: line_models.LineState(
                    fluid_mass=fluid_masses[name],
                    internal_energy=self.internal_energy_per_line[name],
                )
                for name in self.lines
            }
        )

        tank_pressures = {name: inlet.pressure for name, inlet in inlet_states.items()}
        tank_temperatures = {
            name: inlet.temperature for name, inlet in inlet_states.items()
        }
        for name in self.lines:
            self.tank_pressure_per_line[name].append(tank_pressures[name])
            self.tank_temperature_per_line[name].append(tank_temperatures[name])

        is_feeding = (
            not self.end_burn
            and all(fluid_mass > 0 for fluid_mass in fluid_masses.values())
            and all(pressure > chamber_pressure for pressure in tank_pressures.values())
        )
        injector_flows = functools.partial(
            get_injector_mass_flows,
            injector=self.motor.thrust_chamber.injector,
            inlet_states=inlet_states,
            line_masses=fluid_masses,
            is_feeding=is_feeding,
            d_t=d_t,
        )
        mass_flows = injector_flows(chamber_pressure)
        for name, mass_flow in mass_flows.items():
            self.mass_flow_rate_per_line[name].append(mass_flow)
        mass_consumed = {name: flow * d_t for name, flow in mass_flows.items()}

        mixture_ratio = self._get_mixture_ratio(mass_flows)
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
            propellant_mass_flow_rate=sum(mass_flows.values()),
            nozzle=nozzle,
            propellant_properties=propellant_properties,
            fluid_mass_per_line=fluid_masses,
            mass_flow_rate_per_line=mass_flows,
            oxidizer_to_fuel_ratio=oxidizer_to_fuel_ratio,
            tank_pressure_per_line=tank_pressures,
            tank_temperature_per_line=tank_temperatures,
        )
        self._apply_nozzle_losses(
            ideal_momentum_term,
            ideal_pressure_term,
            timestep_conditions,
            chamber_pressure,
        )

        if (
            not is_feeding
            or any(mass_consumed[name] >= fluid_masses[name] for name in self.lines)
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

        for name, line in self.lines.items():
            self.fluid_mass_per_line[name].append(
                fluid_masses[name] - mass_consumed[name]
            )
            self.internal_energy_per_line[name] = self._drain_internal_energy(
                tank=line.tank,
                internal_energy=self.internal_energy_per_line[name],
                fluid_mass=fluid_masses[name],
                mass_drained=mass_consumed[name],
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
