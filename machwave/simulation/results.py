from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import IO, Any, Generic, TypeAlias, TypeVar

import numpy as np
import numpy.typing as npt

import machwave.core.performance as performance
import machwave.simulation.states as simulation_states

SimulationResultArray: TypeAlias = npt.NDArray[np.float64]

StateT = TypeVar("StateT", bound=simulation_states.MotorState)


@dataclass(frozen=True, kw_only=True)
class SimulationResult(ABC, Generic[StateT]):
    """Results of a finished internal ballistics simulation."""

    time: SimulationResultArray
    propellant_mass: SimulationResultArray
    chamber_pressure: SimulationResultArray
    exit_pressure: SimulationResultArray
    thrust_coefficient: SimulationResultArray
    ideal_thrust_coefficient: SimulationResultArray
    thrust: SimulationResultArray
    nozzle_efficiency: SimulationResultArray
    loss_fractions: dict[str, SimulationResultArray]
    loss_labels: dict[str, str]
    # None when the run terminated with propellant remaining.
    burn_time: float | None
    thrust_time: float
    end_thrust: bool
    end_burn: bool
    initial_propellant_mass: float
    total_impulse: float
    specific_impulse: float

    @classmethod
    def from_state(cls, state: StateT) -> "SimulationResult":
        """Build a `SimulationResult` from a finished motor state."""
        return cls(
            **cls._collect_base_fields(state),
            **cls._collect_extra_fields(state),
        )

    @classmethod
    def _collect_base_fields(cls, state: StateT) -> dict[str, Any]:
        time = np.asarray(state.time)
        thrust = np.asarray(state.thrust)
        total_impulse = performance.get_total_impulse(thrust, time)
        initial_propellant_mass = state.motor.initial_propellant_mass
        return {
            "time": time,
            "propellant_mass": np.asarray(state.propellant_mass),
            "chamber_pressure": np.asarray(state.chamber_pressure),
            "exit_pressure": np.asarray(state.exit_pressure),
            "thrust_coefficient": np.asarray(state.thrust_coefficient),
            "ideal_thrust_coefficient": np.asarray(state.ideal_thrust_coefficient),
            "thrust": thrust,
            "nozzle_efficiency": np.asarray(state.nozzle_efficiency),
            "loss_fractions": {
                name: np.asarray(series)
                for name, series in state.loss_fractions.items()
            },
            "loss_labels": dict(state.motor.nozzle_loss_model.component_labels),
            "burn_time": state.burn_time,
            "thrust_time": state.thrust_time,
            "end_thrust": state.end_thrust,
            "end_burn": state.end_burn,
            "initial_propellant_mass": initial_propellant_mass,
            "total_impulse": total_impulse,
            "specific_impulse": performance.get_specific_impulse(
                total_impulse=total_impulse,
                initial_propellant_mass=initial_propellant_mass,
            ),
        }

    @classmethod
    @abstractmethod
    def _collect_extra_fields(cls, state: StateT) -> dict[str, Any]:
        """Build constructor kwargs for fields specific to the subclass."""

    def report(self, file: IO = sys.stdout) -> None:
        """Print a human-readable report of the simulation result."""
        print("\nINTERNAL BALLISTICS SIMULATION RESULTS", file=file)
        self._report_body(file)

    @abstractmethod
    def _report_body(self, file: IO) -> None:
        """Print the subclass-specific portion of the report."""

    def _report_nozzle_losses(self, file: IO) -> None:
        """Print the nozzle efficiency and each loss component's mean fraction."""
        print("\nNOZZLE", file=file)
        print(
            f"  Average nozzle efficiency: {np.mean(self.nozzle_efficiency):.3%}",
            file=file,
        )
        for name, series in self.loss_fractions.items():
            label = self.loss_labels[name]
            print(f"  Average {label} fraction: {np.mean(series):.3%}", file=file)

    def _format_burn_time(self, decimals: int = 3) -> str:
        """Format the burn time for a report, or flag it as never reached."""
        if self.burn_time is None:
            return "not reached"
        return f"{self.burn_time:.{decimals}f} s"

    def summary(self) -> dict[str, float | None]:
        """Return a mapping of headline scalar metrics for this result."""
        return {
            "burn_time": self.burn_time,
            "thrust_time": self.thrust_time,
            "initial_propellant_mass": self.initial_propellant_mass,
            "total_impulse": self.total_impulse,
            "specific_impulse": self.specific_impulse,
            "peak_chamber_pressure": float(np.max(self.chamber_pressure)),
            "mean_chamber_pressure": float(np.mean(self.chamber_pressure)),
            "peak_thrust": float(np.max(self.thrust)),
            "mean_thrust": float(np.mean(self.thrust)),
            **self._extra_summary(),
        }

    def _extra_summary(self) -> dict[str, float]:
        """Return subclass-specific scalar metrics to merge into `summary()`."""
        return {}
