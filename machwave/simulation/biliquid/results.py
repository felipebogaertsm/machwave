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

    fluid_mass_per_line: dict[str, simulation_results.SimulationResultArray]
    tank_pressure_per_line: dict[str, simulation_results.SimulationResultArray]
    # Flat for an isothermal tank, decaying for one running an energy balance.
    tank_temperature_per_line: dict[str, simulation_results.SimulationResultArray]
    final_fluid_mass_per_line: dict[str, float]

    @classmethod
    def _collect_extra_fields(
        cls, state: "biliquid_states.BiliquidEngineState"
    ) -> dict[str, Any]:
        fluid_mass_per_line = {
            name: np.asarray(series)
            for name, series in state.fluid_mass_per_line.items()
        }
        return {
            "fluid_mass_per_line": fluid_mass_per_line,
            "tank_pressure_per_line": {
                name: np.asarray(series)
                for name, series in state.tank_pressure_per_line.items()
            },
            "tank_temperature_per_line": {
                name: np.asarray(series)
                for name, series in state.tank_temperature_per_line.items()
            },
            "final_fluid_mass_per_line": {
                name: float(series[-1]) for name, series in fluid_mass_per_line.items()
            },
        }

    def _extra_summary(self) -> dict[str, float]:
        return {
            f"final_{name}_mass": mass
            for name, mass in self.final_fluid_mass_per_line.items()
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
        label_width = max(len(name) for name in self.final_fluid_mass_per_line)
        for name, mass in self.final_fluid_mass_per_line.items():
            print(
                f"  {name.capitalize() + ':':<{label_width + 1}} {mass:.4f}", file=file
            )
