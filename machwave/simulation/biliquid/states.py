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

# Of the no-loss flow. Lands within about 1e-9 of the exact root, far below
# what any orifice model is good for, in two element evaluations fewer than
# brentq's default tolerance.
FLOW_SOLVE_RELATIVE_TOLERANCE = 1e-8


def get_line_mass_flow(
    chamber_pressure: float,
    *,
    element: injector_models.InjectorElement,
    line: line_models.PropellantLine,
    head_state: fluid_state_models.FluidState,
) -> float:
    """
    Flow a line delivers through its injector element [kg/s].

    The feedline loses pressure with its own flow, so the element sees
    P_head - dP(mdot) and the flow solves

        mdot = f_inj(P_head - dP(mdot), Pc)

    The right-hand side falls as mdot rises, so the root is unique and lies
    between zero and the flow the element passes with no line loss. An SPI
    element is a second quadratic resistance in series with the line, so its
    root has a closed form; any other element is solved by bracketing.

    Args:
        chamber_pressure: Chamber pressure [Pa].
        element: Injector element the line flows through.
        line: Propellant line, whose resistance sets the feedline loss.
        head_state: Propellant state at the head of the feedline, with no
            line loss taken.

    Returns:
        Mass flow rate of the line [kg/s].
    """
    lossless_flow = element.get_mass_flow(
        inlet=head_state, chamber_pressure=chamber_pressure
    )
    resistance = line.resistance
    if resistance is None or lossless_flow <= 0.0:
        return lossless_flow

    if element.mass_flow_model == injector_models.MassFlowModel.SPI:
        # mdot = Cd A sqrt(2 rho dP_orifice) and the line takes
        # K mdot^2 / (2 rho A_line^2) of the same head-to-chamber drop.
        return lossless_flow / math.sqrt(
            1.0
            + resistance.loss_coefficient
            * (element.discharge_coefficient * element.area / resistance.flow_area) ** 2
        )

    # brentq evaluates both ends of the bracket again, and each evaluation of
    # an element such as HEM is a CoolProp sweep, so keep what is known.
    residuals = {0.0: -lossless_flow}

    def get_flow_residual(mass_flow: float) -> float:
        if mass_flow not in residuals:
            inlet = fluid_state_models.FluidState(
                fluid_name=head_state.fluid_name,
                pressure=head_state.pressure
                - line.get_pressure_drop(mass_flow, head_state.density),
                temperature=head_state.temperature,
                density=head_state.density,
            )
            residuals[mass_flow] = mass_flow - element.get_mass_flow(
                inlet=inlet, chamber_pressure=chamber_pressure
            )
        return residuals[mass_flow]

    if get_flow_residual(lossless_flow) <= 0.0:
        # The element passes no less at the lower inlet pressure, as HEM from
        # a saturated inlet does: its stagnation state is the saturated liquid
        # at the tank temperature whatever the pressure, so the line loss
        # leaves the flow alone.
        return lossless_flow

    return cast(
        float,
        scipy.optimize.brentq(
            get_flow_residual,
            0.0,
            lossless_flow,
            xtol=FLOW_SOLVE_RELATIVE_TOLERANCE * lossless_flow,
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

    Each line's flow is solved with its own feedline loss. No line delivers
    more than the mass it has left over the timestep.

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

    missing = [name for name in injector.elements if name not in inlet_states]
    if missing:
        raise ValueError(f"no inlet state was given for {missing}")

    return {
        name: min(
            get_line_mass_flow(
                chamber_pressure,
                element=element,
                line=lines[name],
                head_state=inlet_states[name],
            ),
            line_masses[name] / d_t,
        )
        for name, element in injector.elements.items()
    }


def get_internal_energy_rate(
    *,
    outflow_specific_enthalpy: float,
    mass_flow_rate: float,
    pressure: float,
    volume_rate: float,
) -> float:
    """
    Rate of change of the internal energy of an adiabatic tank [W].

    The open-system energy balance of a tank that loses fluid through one port
    and whose boundary moves, as a piston does:

        dU/dt = -h_out * mdot_out - P * dV/dt

    The first term is the enthalpy the leaving fluid carries, which includes
    the flow work that pushes it out. The second is the boundary work the
    fluid does on a moving wall. A tank of fixed volume has dV/dt = 0.

    Args:
        outflow_specific_enthalpy: Specific enthalpy of the leaving fluid
            [J/kg].
        mass_flow_rate: Mass flow leaving the tank [kg/s] (>=0).
        pressure: Tank pressure [Pa].
        volume_rate: Rate at which the volume the fluid fills grows [m^3/s].

    Returns:
        dU/dt [W].
    """
    return -outflow_specific_enthalpy * mass_flow_rate - pressure * volume_rate


def get_total_injector_mass_flow(
    chamber_pressure: float,
    *,
    injector_flows: Callable[[float], Mapping[str, float]],
) -> float:
    """Total injector mass flow over every line at the given pressure [kg/s]."""
    return sum(injector_flows(chamber_pressure).values())


class _StageLeftTheStateSpaceError(Exception):
    """A Runge-Kutta stage drained a line past empty."""


@dataclasses.dataclass(frozen=True, kw_only=True)
class _CoupledStateLayout:
    """
    Where every variable of the biliquid engine sits in the integrated vector.

    The vector is (P_c, m_i for every line, U_j for every tank that runs an
    energy balance), in the order the lines are given.
    """

    line_names: tuple[str, ...]
    energy_line_names: tuple[str, ...]

    def mass_index(self, name: str) -> int:
        """Index of the fluid mass of a line."""
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
        """Pack the engine state into one vector."""
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

        initial_states = feed_system.get_initial_line_states()
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
        # A flow capped at line_mass / d_t can round to more than the line holds
        mass_consumed = {
            name: min(flow * d_t, fluid_masses[name])
            for name, flow in mass_flows.items()
        }

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
        step_count = rk4.get_stable_step_count(
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

        depletes_this_step = any(
            mass_consumed[name] >= fluid_masses[name] for name in self.lines
        )
        if is_feeding and depletes_this_step:
            self._run_depletion_step(
                d_t=d_t,
                step_count=step_count,
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
        )
        try:
            new_state = rk4.rk4th_vector_ode_solver(
                state,
                equation,
                d_t,
                step_count=step_count,
                initial_derivative=equation(
                    state,
                    known=(inlet_states, mass_flows, propellant_properties),
                ),
            )
        except _StageLeftTheStateSpaceError:
            new_state = None
        if new_state is None or any(
            mass <= 0.0 for mass in layout.unpack_masses(new_state).values()
        ):
            # A line ran dry inside a stage, though not at the start of the
            # step: take the step the depletion step takes.
            self._run_depletion_step(
                d_t=d_t,
                step_count=step_count,
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
        known: tuple[
            Mapping[str, fluid_state_models.FluidState],
            Mapping[str, float],
            propellant_properties_models.ThermochemicalProperties,
        ]
        | None = None,
    ) -> npt.NDArray[np.float64]:
        """
        Time derivative of the whole engine state at one Runge-Kutta stage.

        The state is y = (P_c, m_i for every line, U_j for every tank that
        runs an energy balance), and

            dP_c/dt = R T / V_c (sum_i mdot_i - mdot_nozzle)
            dm_i/dt = -mdot_i
            dU_j/dt = -h_out,j mdot_j - P_j dV_j/dt

        with every term read at the stage state: the feedline head states from
        the stage (m, U), each line flow solved at the stage P_c, and the
        thermochemistry at the stage P_c and mixture ratio, through the
        propellant's quantized cache. Nothing is frozen at the start of the
        step, which is what keeps the step fourth order.

        Args:
            state: Packed state vector.
            layout: Where every variable sits in the vector.
            is_feeding: Whether the feed system delivers over this step. It is
                decided at the start of the step, so a line that stops feeding
                stops at a step boundary.
            external_pressure: Ambient pressure [Pa].
            known: Feedline head states, line flows and propellant properties
                already evaluated at this state, at the start of the step.

        Returns:
            dy/dt, packed like the state.

        Raises:
            _StageLeftTheStateSpaceError: If a stage has a line with no mass
                left, where neither the tank model nor the flow is defined.
        """
        chamber_pressure = float(state[0])
        fluid_masses = layout.unpack_masses(state)
        internal_energies = {
            **self.internal_energy_per_line,
            **layout.unpack_energies(state),
        }
        derivative = np.zeros_like(state)
        if not is_feeding:
            # Nothing leaves the tanks, so only the chamber moves.
            mass_flows = {name: 0.0 for name in self.lines}
            propellant_properties = (
                known[2]
                if known is not None
                else self._evaluate_propellant_properties(chamber_pressure, None)
            )
        else:
            if any(fluid_mass <= 0.0 for fluid_mass in fluid_masses.values()):
                raise _StageLeftTheStateSpaceError
            feed_system = self.motor.feed_system
            if known is not None:
                inlet_states, mass_flows, propellant_properties = known
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
                mass_flows = {
                    name: get_line_mass_flow(
                        chamber_pressure,
                        element=element,
                        line=self.lines[name],
                        head_state=inlet_states[name],
                    )
                    for name, element in (
                        self.motor.thrust_chamber.injector.elements.items()
                    )
                }
                propellant_properties = self._evaluate_propellant_properties(
                    chamber_pressure, self._get_mixture_ratio(mass_flows)
                )

            volume_rates = feed_system.get_tank_volume_rates(fluid_masses, mass_flows)
            volumes = feed_system.get_tank_volumes(fluid_masses)
            for name in layout.energy_line_names:
                tank = self.lines[name].tank
                derivative[layout.energy_index(name)] = get_internal_energy_rate(
                    # The rate form drains an infinitesimal mass, which is
                    # liquid while any liquid is left.
                    outflow_specific_enthalpy=tank.get_outflow_specific_enthalpy(
                        fluid_masses[name],
                        internal_energies[name],
                        mass_drained=0.0,
                        volume=volumes[name],
                    ),
                    mass_flow_rate=mass_flows[name],
                    pressure=(
                        tank.get_pressure(
                            fluid_masses[name],
                            internal_energies[name],
                            volume=volumes[name],
                        )
                        if volume_rates[name] != 0.0
                        else 0.0
                    ),
                    volume_rate=volume_rates[name],
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
        step_count: int,
        external_pressure: float,
        chamber_pressure: float,
        fluid_masses: Mapping[str, float],
        mass_consumed: Mapping[str, float],
        injector_flows: Callable[[float], Mapping[str, float]],
        propellant_properties: propellant_properties_models.ThermochemicalProperties,
    ) -> None:
        """
        Take the step on which a line runs dry, first order.

        Burnout is an event inside the step, which no fixed-step Runge-Kutta
        stage can straddle at its order, and a stage past it would read a tank
        with negative mass. The step therefore drains each line by its flow at
        the start of the step, capped at what the line holds, so a line that
        runs out lands on zero exactly, and steps the internal energy with the
        same flows. The chamber pressure goes through RK4 with the feedline
        head states and the thermochemistry of the start of the step.

        Args:
            d_t: Time increment [s].
            step_count: Number of RK4 steps the chamber stiffness needs.
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
                step_count=step_count,
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
                d_t=d_t,
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
        d_t: float,
    ) -> float | None:
        """
        Step the internal energy of a tank over one timestep [J].

        The tank is adiabatic. It loses the enthalpy of what it drains, and
        where its boundary moves it does the work P dV on it, both taken at the
        start of the step like the mass update. The fluid behind boils to
        refill the space and cools doing it, which is what walks the saturation
        pressure down over the burn.

        Args:
            tank: Tank of the line.
            internal_energy: Internal energy at the start of the step [J].
            fluid_mass: Fluid mass at the start of the step [kg].
            mass_drained: Mass drained over the step [kg].
            volume: Volume the fluid fills at the start of the step [m^3].
            swept_volume: How much that volume grows over the step [m^3].
            d_t: Time increment [s].

        Returns:
            The internal energy left in the tank [J], or None for a line that
            runs no energy balance.
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
        pressure = (
            tank.get_pressure(fluid_mass, internal_energy, volume=volume)
            if swept_volume != 0.0
            else 0.0
        )
        return internal_energy + d_t * get_internal_energy_rate(
            outflow_specific_enthalpy=outflow_specific_enthalpy,
            mass_flow_rate=mass_drained / d_t,
            pressure=pressure,
            volume_rate=swept_volume / d_t,
        )
