from __future__ import annotations

import math
from dataclasses import dataclass
from typing import IO, TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt

import machwave.simulation.results as simulation_results

if TYPE_CHECKING:
    import machwave.simulation.biliquid.states as biliquid_states


@dataclass(frozen=True, kw_only=True)
class BiliquidSimulationResult(
    simulation_results.SimulationResult["biliquid_states.BiliquidEngineState"]
):
    """
    Simulation result for a biliquid engine run.

    Per-line series are keyed by line name and hold one value per entry of
    `time`.
    """

    fluid_mass_per_line: dict[str, simulation_results.SimulationResultArray]
    # Injector flow of each line [kg/s], zero once the feed has stopped.
    mass_flow_rate_per_line: dict[str, simulation_results.SimulationResultArray]
    # Total oxidizer flow over total fuel flow. NaN where either side has
    # stopped flowing, since the ratio has no meaning there.
    oxidizer_to_fuel_ratio: simulation_results.SimulationResultArray
    tank_pressure_per_line: dict[str, simulation_results.SimulationResultArray]
    # Flat for an isothermal tank, decaying for one running an energy balance.
    tank_temperature_per_line: dict[str, simulation_results.SimulationResultArray]
    final_fluid_mass_per_line: dict[str, float]
    # Oxidizer mass delivered over fuel mass delivered. NaN if no fuel left a
    # tank. A time mean of `oxidizer_to_fuel_ratio` would not do: it blows up
    # as the last of one side trickles out.
    mean_oxidizer_to_fuel_ratio: float

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
            "mass_flow_rate_per_line": {
                name: np.asarray(series)
                for name, series in state.mass_flow_rate_per_line.items()
            },
            "oxidizer_to_fuel_ratio": np.asarray(state.oxidizer_to_fuel_ratio),
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
            "mean_oxidizer_to_fuel_ratio": cls._get_mean_oxidizer_to_fuel_ratio(
                fluid_mass_per_line,
                oxidizer_line_names=state.oxidizer_line_names,
                fuel_line_names=state.fuel_line_names,
            ),
        }

    @staticmethod
    def _get_mean_oxidizer_to_fuel_ratio(
        fluid_mass_per_line: dict[str, simulation_results.SimulationResultArray],
        *,
        oxidizer_line_names: tuple[str, ...],
        fuel_line_names: tuple[str, ...],
    ) -> float:
        """
        Oxidizer mass delivered over fuel mass delivered during the run.

        Nothing flows after the burn, so this is the mean over the burn,
        weighted by fuel flow. Steps where the ratio is NaN carry no flow and
        drop out.

        Returns:
            The ratio, or NaN when no fuel was delivered.
        """

        def delivered(names: tuple[str, ...]) -> float:
            return sum(
                float(fluid_mass_per_line[name][0] - fluid_mass_per_line[name][-1])
                for name in names
            )

        fuel_delivered = delivered(fuel_line_names)
        if fuel_delivered <= 0.0:
            return math.nan
        return delivered(oxidizer_line_names) / fuel_delivered

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

        print("\nMIXTURE RATIO", file=file)
        print(
            f"  Mean O/F over the burn: {self.mean_oxidizer_to_fuel_ratio:.4f}",
            file=file,
        )

        burning = self._burn_mask()
        label_width = max(len(name) for name in self.mass_flow_rate_per_line)
        print("\nMEAN MASS FLOW OVER THE BURN (kg/s)", file=file)
        for name, series in self.mass_flow_rate_per_line.items():
            print(
                f"  {name.capitalize() + ':':<{label_width + 1}} "
                f"{np.mean(series[burning]):.4f}",
                file=file,
            )

        print("\nPROPELLANT REMAINING (kg)", file=file)
        for name, mass in self.final_fluid_mass_per_line.items():
            print(
                f"  {name.capitalize() + ':':<{label_width + 1}} {mass:.4f}", file=file
            )

    def _burn_mask(self) -> npt.NDArray[np.bool_]:
        """
        Timesteps that fall inside the burn.

        The whole run when the burn never ended, so the means stay defined.
        """
        if self.burn_time is None:
            return np.ones_like(self.time, dtype=bool)
        return self.time < self.burn_time
