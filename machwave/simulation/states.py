from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeAlias

from machwave.models.motors import Motor

if TYPE_CHECKING:
    from machwave.simulation.results import SimulationResult

SimulationStateArray: TypeAlias = list[float]


class MotorState(ABC):
    """Defines the states and iteration step for a motor operation."""

    result_class: ClassVar[type["SimulationResult"]]

    def __init__(
        self,
        motor: Motor,
        igniter_pressure: float,
        external_pressure: float,
        other_losses: float,
    ) -> None:
        self.motor = motor
        self.other_losses = other_losses

        self.time: SimulationStateArray = [0.0]

        self.propellant_mass: SimulationStateArray = [motor.initial_propellant_mass]
        self.chamber_pressure: SimulationStateArray = [igniter_pressure]
        self.exit_pressure: SimulationStateArray = [external_pressure]

        self.thrust_coefficient: SimulationStateArray = [0.0]
        self.ideal_thrust_coefficient: SimulationStateArray = [0.0]
        self.thrust: SimulationStateArray = [0.0]

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

    def build_result(self) -> "SimulationResult":
        """Return a frozen ``SimulationResult`` snapshot of this state."""
        return self.result_class.from_state(self)

    @property
    def initial_propellant_mass(self) -> float:
        return self.motor.initial_propellant_mass

    @property
    def thrust_time(self) -> float:
        if self._thrust_time is None:
            raise ValueError("Thrust time has not been set, run the simulation.")
        return self._thrust_time

    @property
    def burn_time(self) -> float:
        if self._burn_time is None:
            raise ValueError("Burn time has not been set, run the simulation.")
        return self._burn_time
