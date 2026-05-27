from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeAlias

import machwave.models.motors as motors

if TYPE_CHECKING:
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
        other_losses: float,
    ) -> None:
        """
        Initialize a motor state.

        Args:
            motor: Motor to track.
            igniter_pressure: Initial chamber pressure from the igniter [Pa].
            external_pressure: Ambient pressure [Pa].
            other_losses: Fractional losses not covered by specific
                mechanisms, in [0, 1].
        """
        self.motor = motor
        self.external_pressure = external_pressure
        self.other_losses = other_losses

        self.time: SimulationStateArray = [0.0]
        self.chamber_pressure: SimulationStateArray = [igniter_pressure]

        self.propellant_mass: SimulationStateArray = []
        self.exit_pressure: SimulationStateArray = []
        self.ideal_thrust_coefficient: SimulationStateArray = []
        self.thrust_coefficient: SimulationStateArray = []
        self.thrust: SimulationStateArray = []

        self._thrust_time: float | None = None
        self._burn_time: float | None = None

        self.end_thrust: bool = False
        self.end_burn: bool = False

    @abstractmethod
    def get_m_dot_in(self) -> float:
        """Mass flow rate into the combustion chamber [kg/s]."""

    @abstractmethod
    def run_timestep(self, *args, **kwargs) -> None:
        """Advance the per-step accumulators by one time increment."""

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
