from __future__ import annotations

from dataclasses import dataclass
from typing import IO, TYPE_CHECKING, Any

import numpy as np

import machwave.simulation.results as simulation_results

if TYPE_CHECKING:
    import machwave.simulation.biliquid.states as biliquid_states


@dataclass(frozen=True, kw_only=True)
class BiliquidSimulationResult(
    simulation_results.SimulationResult["biliquid_states.BiliquidEngineState"]
):
    """Simulation result for a biliquid engine run."""

    oxidizer_mass: simulation_results.SimulationResultArray
    fuel_mass: simulation_results.SimulationResultArray
    fuel_tank_pressure: simulation_results.SimulationResultArray
    oxidizer_tank_pressure: simulation_results.SimulationResultArray
    # Flat for an isothermal tank, decaying for one running an energy balance.
    fuel_tank_temperature: simulation_results.SimulationResultArray
    oxidizer_tank_temperature: simulation_results.SimulationResultArray
    final_oxidizer_mass: float
    final_fuel_mass: float

    @classmethod
    def _collect_extra_fields(
        cls, state: "biliquid_states.BiliquidEngineState"
    ) -> dict[str, Any]:
        oxidizer_mass = np.asarray(state.oxidizer_mass)
        fuel_mass = np.asarray(state.fuel_mass)
        return {
            "oxidizer_mass": oxidizer_mass,
            "fuel_mass": fuel_mass,
            "fuel_tank_pressure": np.asarray(state.fuel_tank_pressure),
            "oxidizer_tank_pressure": np.asarray(state.oxidizer_tank_pressure),
            "fuel_tank_temperature": np.asarray(state.fuel_tank_temperature),
            "oxidizer_tank_temperature": np.asarray(state.oxidizer_tank_temperature),
            "final_oxidizer_mass": float(oxidizer_mass[-1]),
            "final_fuel_mass": float(fuel_mass[-1]),
        }

    def _extra_summary(self) -> dict[str, float]:
        return {
            "final_oxidizer_mass": self.final_oxidizer_mass,
            "final_fuel_mass": self.final_fuel_mass,
        }

    def _report_body(self, file: IO) -> None:
        print("\nBILIQUID ENGINE OPERATION RESULTS", file=file)

        print(f"Initial propellant mass: {self.propellant_mass[0]:.4f} kg", file=file)
        print(f"Burnout time: {self._format_burn_time(decimals=4)}", file=file)
        print(f"Thrust time: {self.thrust_time:.4f} s", file=file)

        print("\nCHAMBER PRESSURE (MPa)", file=file)
        print(f"  Max: {np.max(self.chamber_pressure) * 1e-6:.4f}", file=file)
        print(f"  Mean: {np.mean(self.chamber_pressure) * 1e-6:.4f}", file=file)

        print("\nTHRUST (N)", file=file)
        print(f"  Max: {np.max(self.thrust):.4f}", file=file)
        print(f"  Mean: {np.mean(self.thrust):.4f}", file=file)

        print("\nIMPULSE AND I_SP", file=file)
        print(f"  Total impulse: {self.total_impulse:.4f} N-s", file=file)
        print(f"  Specific impulse: {self.specific_impulse:.4f} s", file=file)

        self._report_nozzle_losses(file)

        print("\nPROPELLANT REMAINING (kg)", file=file)
        print(f"  Oxidizer: {self.final_oxidizer_mass:.4f}", file=file)
        print(f"  Fuel:     {self.final_fuel_mass:.4f}", file=file)
