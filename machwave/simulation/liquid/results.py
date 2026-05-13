from __future__ import annotations

from dataclasses import dataclass
from typing import IO, TYPE_CHECKING, Any

import numpy as np

from machwave.simulation.results import SimulationResult, SimulationResultArray

if TYPE_CHECKING:
    from machwave.simulation.liquid.states import LiquidEngineState


@dataclass(frozen=True, kw_only=True)
class LiquidSimulationResult(SimulationResult["LiquidEngineState"]):
    oxidizer_mass: SimulationResultArray
    fuel_mass: SimulationResultArray
    nozzle_correction_factor: SimulationResultArray
    fuel_tank_pressure: SimulationResultArray
    oxidizer_tank_pressure: SimulationResultArray
    final_oxidizer_mass: float
    final_fuel_mass: float

    @classmethod
    def _collect_extra_fields(cls, state: "LiquidEngineState") -> dict[str, Any]:
        oxidizer_mass = np.asarray(state.oxidizer_mass)
        fuel_mass = np.asarray(state.fuel_mass)
        return {
            "oxidizer_mass": oxidizer_mass,
            "fuel_mass": fuel_mass,
            "nozzle_correction_factor": np.asarray(state.nozzle_correction_factor),
            "fuel_tank_pressure": np.asarray(state.fuel_tank_pressure),
            "oxidizer_tank_pressure": np.asarray(state.oxidizer_tank_pressure),
            "final_oxidizer_mass": float(oxidizer_mass[-1]),
            "final_fuel_mass": float(fuel_mass[-1]),
        }

    def _extra_summary(self) -> dict[str, float]:
        return {
            "final_oxidizer_mass": self.final_oxidizer_mass,
            "final_fuel_mass": self.final_fuel_mass,
        }

    def _report_body(self, file: IO) -> None:
        print("\nLIQUID ENGINE OPERATION RESULTS", file=file)

        print(f"Initial propellant mass: {self.propellant_mass[0]:.4f} kg", file=file)
        print(f"Burnout time: {self.burn_time:.4f} s", file=file)
        print(f"Thrust time: {self.thrust_time:.4f} s", file=file)

        print("\nCHAMBER PRESSURE (MPa)", file=file)
        print(f"  Max: {np.max(self.chamber_pressure) * 1e-6:.4f}", file=file)
        print(f"  Mean: {np.mean(self.chamber_pressure) * 1e-6:.4f}", file=file)

        print("\nTHRUST (N)", file=file)
        print(f"  Max: {np.max(self.thrust):.4f}", file=file)
        print(f"  Mean: {np.mean(self.thrust):.4f}", file=file)

        print("\nIMPULSE AND I_SP", file=file)
        print(f"  Total impulse: {self.total_impulse:.4f} N·s", file=file)
        print(f"  Specific impulse: {self.specific_impulse:.4f} s", file=file)

        print("\nPROPELLANT REMAINING (kg)", file=file)
        print(f"  Oxidizer: {self.final_oxidizer_mass:.4f}", file=file)
        print(f"  Fuel:     {self.final_fuel_mass:.4f}", file=file)
