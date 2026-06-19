from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeAlias

import machwave.core.compressible_flow.nozzle as nozzle_core
import machwave.models.motors as motors

if TYPE_CHECKING:
    import machwave.models.propellants.properties as propellant_properties_models
    import machwave.models.thrust_chamber as thrust_chamber_models
    import machwave.simulation.results as simulation_results

SimulationStateArray: TypeAlias = list[float]


class MotorState(ABC):
    """Defines the states and iteration step for a motor operation."""

    result_class: ClassVar[type["simulation_results.SimulationResult"]]

    def __init__(
        self,
        motor: motors.Motor,
        igniter_pressure: float,
        external_pressure: float,
    ) -> None:
        """
        Initialize a motor state.

        Args:
            motor: Motor to track.
            igniter_pressure: Initial chamber pressure from the igniter [Pa].
            external_pressure: Ambient pressure [Pa].
        """
        self.motor = motor
        self.external_pressure = external_pressure

        self.time: SimulationStateArray = [0.0]
        self.chamber_pressure: SimulationStateArray = [igniter_pressure]

        self.propellant_mass: SimulationStateArray = []
        self.exit_pressure: SimulationStateArray = []
        self.ideal_thrust_coefficient: SimulationStateArray = []
        self.thrust_coefficient: SimulationStateArray = []
        self.thrust: SimulationStateArray = []
        self.nozzle_efficiency: SimulationStateArray = []
        self.loss_fractions: dict[str, SimulationStateArray] = {
            name: [] for name in motor.nozzle_loss_model.component_names
        }

        self._thrust_time: float | None = None
        self._burn_time: float | None = None

        self.end_thrust: bool = False
        self.end_burn: bool = False

    @abstractmethod
    def run_timestep(self, *args, **kwargs) -> None:
        """Advance the per-step accumulators by one time increment."""

    def _ideal_thrust_coefficient_terms(
        self,
        k_exhaust: float,
        chamber_pressure: float,
        external_pressure: float,
    ) -> tuple[float, float, float, float]:
        """
        Resolve the separated exit conditions and ideal thrust-coefficient terms.

        Appends the effective exit pressure and the ideal thrust coefficient for the
        timestep.

        Args:
            k_exhaust: Isentropic exponent at the nozzle exit.
            chamber_pressure: Chamber pressure [Pa].
            external_pressure: Ambient pressure [Pa].

        Returns:
            The effective expansion ratio, effective exit pressure [Pa], and the
            momentum and pressure terms of the ideal thrust coefficient.
        """
        nozzle = self.motor.thrust_chamber.nozzle
        effective_expansion_ratio, exit_pressure = (
            nozzle_core.get_separated_exit_conditions(
                k_exhaust,
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
                k_exhaust,
            )
        )
        self.ideal_thrust_coefficient.append(momentum_term + pressure_term)
        return effective_expansion_ratio, exit_pressure, momentum_term, pressure_term

    def _apply_nozzle_losses(
        self,
        momentum_term: float,
        pressure_term: float,
        timestep_conditions: TimestepConditions,
        chamber_pressure: float,
    ) -> None:
        """
        Derate the ideal thrust-coefficient terms and record the loss outputs.

        Appends the realized nozzle efficiency, each component loss fraction, the
        corrected thrust coefficient, and the thrust for the timestep.

        Args:
            momentum_term: Momentum term of the ideal thrust coefficient.
            pressure_term: Pressure term of the ideal thrust coefficient.
            timestep_conditions: Engine conditions for the loss components.
            chamber_pressure: Chamber pressure [Pa].
        """
        nozzle = self.motor.thrust_chamber.nozzle
        loss_result = self.motor.nozzle_loss_model.evaluate(
            momentum_term, pressure_term, timestep_conditions
        )
        self.nozzle_efficiency.append(loss_result.nozzle_efficiency)
        for name, fraction in loss_result.loss_fractions.items():
            self.loss_fractions[name].append(fraction)

        thrust_coefficient = loss_result.momentum_term + loss_result.pressure_term
        self.thrust_coefficient.append(thrust_coefficient)
        thrust = nozzle_core.get_thrust_from_thrust_coefficient(
            thrust_coefficient, chamber_pressure, nozzle.get_throat_area()
        )
        self.thrust.append(thrust)

    def build_result(self) -> "simulation_results.SimulationResult":
        """Return a frozen ``SimulationResult`` snapshot of this state."""
        return self.result_class.from_state(self)

    @property
    def initial_propellant_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        return self.motor.initial_propellant_mass

    @property
    def thrust_time(self) -> float:
        """
        Return the thrust time [s].

        Raises:
            ValueError: If the simulation has not yet completed.
        """
        if self._thrust_time is None:
            raise ValueError("Thrust time has not been set, run the simulation.")
        return self._thrust_time

    @property
    def burn_time(self) -> float:
        """
        Return the burn time [s].

        Raises:
            ValueError: If the simulation has not yet completed.
        """
        if self._burn_time is None:
            raise ValueError("Burn time has not been set, run the simulation.")
        return self._burn_time


@dataclasses.dataclass(frozen=True, kw_only=True)
class TimestepConditions:
    """
    Engine conditions at one simulation timestep, in SI units.

    Holds the scalar operating quantities every engine type computes for the
    step, minus the performance outputs derived from them (thrust, thrust
    coefficient, nozzle efficiency). A nozzle loss component reads whatever it
    needs from here, applying its own unit conversions. Each engine type
    provides its own concrete subclass with the extra quantities it tracks.
    """

    time: float
    chamber_pressure: float
    external_pressure: float
    exit_pressure: float
    # Post-separation value; distinct from nozzle.expansion_ratio (geometric).
    effective_expansion_ratio: float
    free_chamber_volume: float
    propellant_mass: float
    propellant_mass_flow_rate: float
    nozzle: thrust_chamber_models.Nozzle
    propellant_properties: propellant_properties_models.ThermochemicalProperties
