from __future__ import annotations

import dataclasses
import functools
import math
from collections.abc import Mapping
from typing import Callable, cast

import numpy as np
import numpy.typing as npt
import scipy.optimize

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

# relative to the lossless flow, far below the accuracy of any orifice model
LINE_FLOW_RELATIVE_TOLERANCE = 1e-8


def get_line_mass_flow(
    chamber_pressure: float,
    *,
    element: injector_models.InjectorElement,
    resistance: line_models.FeedlineResistance,
    head_state: fluid_state_models.FluidState,
    lossless_flow: float,
) -> float:
    """
    Flow a line delivers through its injector element [kg/s].

    The element sees the head pressure less the feedline loss at the same flow, and
    the flow is solved between zero and the lossless flow. If the element passes no
    less at the lower inlet pressure, as the homogeneous equilibrium model does from
    a saturated inlet, the lossless flow is returned.

    Args:
        chamber_pressure: Chamber pressure [Pa].
        element: Injector element the line flows through.
        resistance: Hydraulic resistance of the feedline.
        head_state: Propellant state at the head of the feedline, with no
            line loss taken.
        lossless_flow: Flow the element passes from the head state [kg/s].

    Returns:
        Mass flow rate of the line [kg/s]. The lossless flow itself when it is not
        positive.
    """
    if lossless_flow <= 0.0:
        return lossless_flow

    def get_flow_residual(mass_flow: float) -> float:
        if mass_flow == 0.0:
            return -lossless_flow
        inlet = fluid_state_models.FluidState(
            fluid_name=head_state.fluid_name,
            pressure=head_state.pressure
            - resistance.get_pressure_drop(mass_flow, head_state.density),
            temperature=head_state.temperature,
            density=head_state.density,
        )
        return mass_flow - element.get_mass_flow(
            inlet=inlet, chamber_pressure=chamber_pressure
        )

    if get_flow_residual(lossless_flow) <= 0.0:
        return lossless_flow

    return cast(
        float,
        scipy.optimize.brentq(
            get_flow_residual,
            0.0,
            lossless_flow,
            xtol=LINE_FLOW_RELATIVE_TOLERANCE * lossless_flow,
        ),
    )


def get_injector_mass_flows(
    chamber_pressure: float,
    *,
    injector: injector_models.Injector,
    lines: Mapping[str, line_models.PropellantLine],
    inlet_states: Mapping[str, fluid_state_models.FluidState],
    line_masses: Mapping[str, float],
    is_feeding: bool,
    d_t: float,
) -> dict[str, float]:
    """
    Injector flow on every line at the given chamber pressure [kg/s].

    A line with a feedline resistance has its flow solved with its own loss. No line
    delivers more than the mass it has left over the timestep.

    Args:
        chamber_pressure: Chamber pressure [Pa].
        injector: Injector, with one element per line.
        lines: Propellant line of every element, keyed by line name.
        inlet_states: Propellant state at the head of every feedline, keyed by
            line name.
        line_masses: Fluid mass left on every line [kg], keyed by line name.
        is_feeding: Whether the feed system is still delivering.
        d_t: Time increment [s].

    Raises:
        ValueError: If any element of the injector has no inlet state.
    """
    if not is_feeding:
        return {name: 0.0 for name in inlet_states}

    lossless_flows = injector.get_mass_flows(
        inlet_states=inlet_states, chamber_pressure=chamber_pressure
    )
    flows = {
        name: (
            flow
            if (resistance := lines[name].resistance) is None
            else get_line_mass_flow(
                chamber_pressure,
                element=injector.elements[name],
                resistance=resistance,
                head_state=inlet_states[name],
                lossless_flow=flow,
            )
        )
        for name, flow in lossless_flows.items()
    }
    return {name: min(flow, line_masses[name] / d_t) for name, flow in flows.items()}


def get_total_injector_mass_flow(
    chamber_pressure: float,
    *,
    injector_flows: Callable[[float], Mapping[str, float]],
) -> float:
    """Total injector mass flow over every line at the given pressure [kg/s]."""
    return sum(injector_flows(chamber_pressure).values())


class _LineRanDryAtStageError(Exception):
    """A Runge-Kutta stage drained a line past empty."""


@dataclasses.dataclass(frozen=True, kw_only=True)
class _CoupledStateLayout:
    """
    Position of every variable in the integrated state vector.

    The chamber pressure comes first, then the fluid mass of every line, then the
    internal energy of every tank that runs an energy balance, in line order.
    """

    line_names: tuple[str, ...]
    energy_line_names: tuple[str, ...]

    def mass_index(self, name: str) -> int:
        return 1 + self.line_names.index(name)

    def energy_index(self, name: str) -> int:
        """Index of the internal energy of a line's tank."""
        return 1 + len(self.line_names) + self.energy_line_names.index(name)

    def pack(
        self,
        chamber_pressure: float,
        fluid_masses: Mapping[str, float],
        internal_energies: Mapping[str, float | None],
    ) -> npt.NDArray[np.float64]:
        return np.array(
            [
                chamber_pressure,
                *(fluid_masses[name] for name in self.line_names),
                *(
                    cast(float, internal_energies[name])
                    for name in self.energy_line_names
                ),
            ],
            dtype=np.float64,
        )

    def unpack_masses(self, state: npt.NDArray[np.float64]) -> dict[str, float]:
        """Fluid mass of every line [kg], keyed by line name."""
        return {name: float(state[self.mass_index(name)]) for name in self.line_names}

    def unpack_energies(self, state: npt.NDArray[np.float64]) -> dict[str, float]:
        """Internal energy of every tank that runs an energy balance [J]."""
        return {
            name: float(state[self.energy_index(name)])
            for name in self.energy_line_names
        }


@dataclasses.dataclass(frozen=True, kw_only=True)
class _StartOfStepEvaluation:
    """What the step has already evaluated at its starting state."""

    inlet_states: Mapping[str, fluid_state_models.FluidState]
    mass_flows: Mapping[str, float]
    propellant_properties: propellant_properties_models.ThermochemicalProperties


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
            lines=self.lines,
            inlet_states=inlet_states,
            line_masses=fluid_masses,
            is_feeding=is_feeding,
            d_t=d_t,
        )
        mass_flows = injector_flows(chamber_pressure)
        for name, mass_flow in mass_flows.items():
            self.mass_flow_rate_per_line[name].append(mass_flow)

        mass_consumed = {
            name: min(flow * d_t, fluid_masses[name])
            for name, flow in mass_flows.items()
        }  # limit mass consumed to the available fluid mass in each line

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

        self.time.append(time + d_t)
        substep_count = rk4.get_substep_count(
            {"chamber_pressure": chamber_pressure},
            mass_balance.compute_chamber_pressure_mass_balance,
            d_t,
            **self._get_chamber_balance_arguments(
                propellant_properties,
                external_pressure=external_pressure,
                mass_flow_in=functools.partial(
                    get_total_injector_mass_flow, injector_flows=injector_flows
                ),
            ),
        )
        self.substep_count.append(substep_count)

        depletes_this_step = any(
            mass_consumed[name] >= fluid_masses[name] for name in self.lines
        )
        if is_feeding and depletes_this_step:
            self._run_depletion_step(
                d_t=d_t,
                substep_count=substep_count,
                external_pressure=external_pressure,
                chamber_pressure=chamber_pressure,
                fluid_masses=fluid_masses,
                mass_consumed=mass_consumed,
                injector_flows=injector_flows,
                propellant_properties=propellant_properties,
            )
            return

        layout = _CoupledStateLayout(
            line_names=tuple(self.lines),
            energy_line_names=tuple(
                name
                for name, internal_energy in self.internal_energy_per_line.items()
                if internal_energy is not None
            ),
        )
        state = layout.pack(
            chamber_pressure, fluid_masses, self.internal_energy_per_line
        )
        equation = functools.partial(
            self._get_coupled_derivative,
            layout=layout,
            is_feeding=is_feeding,
            external_pressure=external_pressure,
            d_t=d_t,
        )
        try:
            new_state = rk4.rk4th_vector_ode_solver(
                state,
                equation,
                d_t,
                step_count=substep_count,
                # reuse the start-of-step flows and thermochemistry as the first stage
                initial_derivative=equation(
                    state,
                    start_of_step=_StartOfStepEvaluation(
                        inlet_states=inlet_states,
                        mass_flows=mass_flows,
                        propellant_properties=propellant_properties,
                    ),
                ),
            )
        except _LineRanDryAtStageError:
            new_state = None
        if new_state is None or any(
            mass <= 0.0 for mass in layout.unpack_masses(new_state).values()
        ):
            # a line ran dry inside a stage
            self._run_depletion_step(
                d_t=d_t,
                substep_count=substep_count,
                external_pressure=external_pressure,
                chamber_pressure=chamber_pressure,
                fluid_masses=fluid_masses,
                mass_consumed=mass_consumed,
                injector_flows=injector_flows,
                propellant_properties=propellant_properties,
            )
            return

        self.chamber_pressure.append(float(new_state[0]))
        for name, fluid_mass in layout.unpack_masses(new_state).items():
            self.fluid_mass_per_line[name].append(fluid_mass)
        self.internal_energy_per_line.update(layout.unpack_energies(new_state))

    def _get_chamber_balance_arguments(
        self,
        propellant_properties: propellant_properties_models.ThermochemicalProperties,
        *,
        external_pressure: float,
        mass_flow_in: Callable[[float], float],
    ) -> dict:
        """Keyword arguments of the chamber mass balance at one set of properties."""
        nozzle = self.motor.thrust_chamber.nozzle
        return dict(
            external_pressure=external_pressure,
            mass_flow_in=mass_flow_in,
            free_chamber_volume=self.motor.thrust_chamber.combustion_chamber.internal_volume,
            throat_area=nozzle.get_throat_area(),
            k=propellant_properties.k_chamber,
            R=propellant_properties.R_chamber,
            flame_temperature=performance.get_effective_flame_temperature(
                adiabatic_flame_temperature=propellant_properties.adiabatic_flame_temperature,
                combustion_efficiency=self.motor.combustion_efficiency,
            ),
            nozzle_discharge_coefficient=nozzle.discharge_coefficient,
        )

    def _get_coupled_derivative(
        self,
        state: npt.NDArray[np.float64],
        *,
        layout: _CoupledStateLayout,
        is_feeding: bool,
        external_pressure: float,
        d_t: float,
        start_of_step: _StartOfStepEvaluation | None = None,
    ) -> npt.NDArray[np.float64]:
        """
        Time derivative of the whole engine state at one Runge-Kutta stage.

        Feedline head states, line flows and thermochemistry are evaluated at the stage
        state.

        Args:
            state: Packed state vector.
            layout: Where every variable sits in the vector.
            is_feeding: Whether the feed system delivers over this step, decided at
                the start of the step.
            external_pressure: Ambient pressure [Pa].
            d_t: Time increment [s], over which no line delivers more than it
                holds.
            start_of_step: Feedline head states, line flows and propellant
                properties already evaluated at `state`, if it is the start of the
                step.

        Returns:
            dy/dt, packed like the state.

        Raises:
            _LineRanDryAtStageError: If a line has no mass left at the stage.
        """
        chamber_pressure = float(state[0])
        fluid_masses = layout.unpack_masses(state)
        internal_energies = {
            **self.internal_energy_per_line,
            **layout.unpack_energies(state),
        }
        derivative = np.zeros_like(state)
        if not is_feeding:
            mass_flows = {name: 0.0 for name in self.lines}
            propellant_properties = (
                start_of_step.propellant_properties
                if start_of_step is not None
                else self._evaluate_propellant_properties(chamber_pressure, None)
            )
        else:
            if any(fluid_mass <= 0.0 for fluid_mass in fluid_masses.values()):
                raise _LineRanDryAtStageError
            feed_system = self.motor.feed_system
            if start_of_step is not None:
                inlet_states = start_of_step.inlet_states
                mass_flows = start_of_step.mass_flows
                propellant_properties = start_of_step.propellant_properties
            else:
                inlet_states = feed_system.get_inlet_states(
                    {
                        name: line_models.LineState(
                            fluid_mass=fluid_masses[name],
                            internal_energy=internal_energies[name],
                        )
                        for name in self.lines
                    }
                )
                mass_flows = get_injector_mass_flows(
                    chamber_pressure,
                    injector=self.motor.thrust_chamber.injector,
                    lines=self.lines,
                    inlet_states=inlet_states,
                    line_masses=fluid_masses,
                    is_feeding=True,
                    d_t=d_t,
                )
                propellant_properties = self._evaluate_propellant_properties(
                    chamber_pressure, self._get_mixture_ratio(mass_flows)
                )

            volume_rates = feed_system.get_tank_volume_rates(fluid_masses, mass_flows)
            volumes = feed_system.get_tank_volumes(fluid_masses)
            for name in layout.energy_line_names:
                tank = self.lines[name].tank
                # an infinitesimal draw is liquid while any liquid is left
                outflow_specific_enthalpy = tank.get_outflow_specific_enthalpy(
                    fluid_masses[name],
                    internal_energies[name],
                    mass_drained=0.0,
                    volume=volumes[name],
                )
                boundary_power = (
                    tank.get_pressure(
                        fluid_masses[name],
                        internal_energies[name],
                        volume=volumes[name],
                    )
                    * volume_rates[name]
                    if volume_rates[name] != 0.0
                    else 0.0
                )
                derivative[layout.energy_index(name)] = (
                    -outflow_specific_enthalpy * mass_flows[name] - boundary_power
                )

        for name, mass_flow in mass_flows.items():
            derivative[layout.mass_index(name)] = -mass_flow
        derivative[0] = mass_balance.compute_chamber_pressure_mass_balance(
            chamber_pressure,
            **self._get_chamber_balance_arguments(
                propellant_properties,
                external_pressure=external_pressure,
                mass_flow_in=lambda _: sum(mass_flows.values()),
            ),
        )[0]
        return derivative

    def _run_depletion_step(
        self,
        *,
        d_t: float,
        substep_count: int,
        external_pressure: float,
        chamber_pressure: float,
        fluid_masses: Mapping[str, float],
        mass_consumed: Mapping[str, float],
        injector_flows: Callable[[float], Mapping[str, float]],
        propellant_properties: propellant_properties_models.ThermochemicalProperties,
    ) -> None:
        """
        Take the step on which a line runs dry, at first order.

        Each line drains by its start-of-step flow, capped at what it holds, so it
        lands on zero. The chamber pressure is integrated with the start-of-step head
        states and thermochemistry.

        Args:
            d_t: Time increment [s].
            substep_count: Number of Runge-Kutta substeps the chamber pressure needs.
            external_pressure: Ambient pressure [Pa].
            chamber_pressure: Chamber pressure at the start of the step [Pa].
            fluid_masses: Fluid mass of every line at the start of the step
                [kg].
            mass_consumed: Mass every line delivers over the step [kg].
            injector_flows: Line flows at a chamber pressure, from the head
                states at the start of the step.
            propellant_properties: Thermochemistry at the start of the step.
        """
        arguments = self._get_chamber_balance_arguments(
            propellant_properties,
            external_pressure=external_pressure,
            mass_flow_in=functools.partial(
                get_total_injector_mass_flow, injector_flows=injector_flows
            ),
        )
        self.chamber_pressure.append(
            rk4.rk4th_vector_ode_solver(
                np.array([chamber_pressure]),
                lambda value: np.array(
                    mass_balance.compute_chamber_pressure_mass_balance(
                        float(value[0]), **arguments
                    )
                ),
                d_t,
                step_count=substep_count,
            )[0]
        )

        feed_system = self.motor.feed_system
        new_fluid_masses = {
            name: fluid_masses[name] - mass_consumed[name] for name in self.lines
        }
        volumes = feed_system.get_tank_volumes(fluid_masses)
        new_volumes = feed_system.get_tank_volumes(new_fluid_masses)
        for name, line in self.lines.items():
            self.fluid_mass_per_line[name].append(new_fluid_masses[name])
            self.internal_energy_per_line[name] = self._drain_internal_energy(
                tank=line.tank,
                internal_energy=self.internal_energy_per_line[name],
                fluid_mass=fluid_masses[name],
                mass_drained=mass_consumed[name],
                volume=volumes[name],
                swept_volume=new_volumes[name] - volumes[name],
            )

    @staticmethod
    def _drain_internal_energy(
        *,
        tank: tank_models.Tank,
        internal_energy: float | None,
        fluid_mass: float,
        mass_drained: float,
        volume: float,
        swept_volume: float,
    ) -> float | None:
        """
        Step the internal energy of a tank over one timestep [J].

        Takes out the enthalpy of the drained fluid and the boundary work of a
        moving tank wall, both evaluated at the start of the step.

        Args:
            tank: Tank of the line.
            internal_energy: Internal energy at the start of the step [J].
            fluid_mass: Fluid mass at the start of the step [kg].
            mass_drained: Mass drained over the step [kg].
            volume: Volume the fluid fills at the start of the step [m^3].
            swept_volume: How much that volume grows over the step [m^3].

        Returns:
            The internal energy left in the tank [J], or None for an
            isothermal tank, which runs no energy balance.
        """
        if internal_energy is None or (mass_drained <= 0.0 and swept_volume == 0.0):
            return internal_energy

        outflow_specific_enthalpy = (
            tank.get_outflow_specific_enthalpy(
                fluid_mass, internal_energy, mass_drained=mass_drained, volume=volume
            )
            if mass_drained > 0.0
            else 0.0
        )
        boundary_work = (
            tank.get_pressure(fluid_mass, internal_energy, volume=volume) * swept_volume
            if swept_volume != 0.0
            else 0.0
        )
        return (
            internal_energy - mass_drained * outflow_specific_enthalpy - boundary_work
        )
