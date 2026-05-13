from __future__ import annotations

from dataclasses import dataclass, field
from typing import IO, TYPE_CHECKING, Any

import numpy as np

import machwave.core.conversions as conversions
from machwave.simulation.results import SimulationResult, SimulationResultArray

if TYPE_CHECKING:
    from machwave.simulation.solid.states import SolidMotorState


@dataclass(frozen=True, kw_only=True)
class SolidSimulationResult(SimulationResult["SolidMotorState"]):
    free_chamber_volume: SimulationResultArray
    web: SimulationResultArray
    burn_area: SimulationResultArray
    propellant_volume: SimulationResultArray
    burn_rate: SimulationResultArray
    divergent_loss: SimulationResultArray
    kinetics_loss: SimulationResultArray
    boundary_layer_loss: SimulationResultArray
    two_phase_loss: SimulationResultArray
    nozzle_efficiency: SimulationResultArray
    overall_efficiency: SimulationResultArray
    propellant_cog: SimulationResultArray
    propellant_moi: SimulationResultArray
    # klemmung is filtered to burn_area > 0, so its length is < len(time).
    klemmung: SimulationResultArray = field(metadata={"non_aligned": True})
    # grain_mass_flux is shaped [segment_count, time_count]; axis 0 is segments.
    grain_mass_flux: SimulationResultArray = field(metadata={"non_aligned": True})
    initial_to_final_klemmung_ratio: float
    volumetric_efficiency: float
    burn_profile: str
    max_mass_flux: float

    @classmethod
    def _collect_extra_fields(cls, state: "SolidMotorState") -> dict[str, Any]:
        motor = state.motor
        nozzle = motor.thrust_chamber.nozzle
        chamber_volume = motor.thrust_chamber.combustion_chamber.internal_volume

        burn_area = np.asarray(state.burn_area)
        propellant_volume = np.asarray(state.propellant_volume)
        burn_rate = np.asarray(state.burn_rate)
        web = np.asarray(state.web)

        klemmung = cls._get_klemmung(burn_area, nozzle.get_throat_area())
        grain_mass_flux = motor.grain.get_mass_flux_per_segment(
            burn_rate, motor.propellant.ideal_density, web
        )

        return {
            "free_chamber_volume": np.asarray(state.free_chamber_volume),
            "web": web,
            "burn_area": burn_area,
            "propellant_volume": propellant_volume,
            "burn_rate": burn_rate,
            "divergent_loss": np.asarray(state.divergent_loss),
            "kinetics_loss": np.asarray(state.kinetics_loss),
            "boundary_layer_loss": np.asarray(state.boundary_layer_loss),
            "two_phase_loss": np.asarray(state.two_phase_loss),
            "nozzle_efficiency": np.asarray(state.nozzle_efficiency),
            "overall_efficiency": np.asarray(state.overall_efficiency),
            "propellant_cog": np.stack(
                [np.asarray(cog) for cog in state.propellant_cog]
            ),
            "propellant_moi": np.stack(
                [np.asarray(moi) for moi in state.propellant_moi]
            ),
            "klemmung": klemmung,
            "grain_mass_flux": grain_mass_flux,
            "initial_to_final_klemmung_ratio": float(klemmung[0] / klemmung[-1]),
            "volumetric_efficiency": cls._get_volumetric_efficiency(
                propellant_volume[0], chamber_volume
            ),
            "burn_profile": cls._classify_burn_profile(klemmung),
            "max_mass_flux": float(np.max(grain_mass_flux)),
        }

    @staticmethod
    def _get_klemmung(
        burn_area: SimulationResultArray, throat_area: float
    ) -> SimulationResultArray:
        """Klemmung (Kn) over non-zero burn-area samples.

        Returns Kn values where burn area is positive; length is <= len(burn_area).
        """
        return burn_area[burn_area > 0] / throat_area

    @staticmethod
    def _classify_burn_profile(
        klemmung: SimulationResultArray, deviancy: float = 0.02
    ) -> str:
        """Classify a burn profile as "regressive", "progressive", or "neutral".

        `deviancy` is the fractional threshold around 1.0 for the initial-to-final
        ratio that delimits the neutral band.
        """
        ratio = float(klemmung[0] / klemmung[-1])
        if ratio > 1 + deviancy:
            return "regressive"
        if ratio < 1 - deviancy:
            return "progressive"
        return "neutral"

    @staticmethod
    def _get_volumetric_efficiency(
        initial_propellant_volume: float, internal_chamber_volume: float
    ) -> float:
        """Fraction of the chamber initially occupied by propellant."""
        return float(initial_propellant_volume / internal_chamber_volume)

    def _extra_summary(self) -> dict[str, float]:
        return {
            "peak_klemmung": float(np.max(self.klemmung)),
            "mean_klemmung": float(np.mean(self.klemmung)),
            "initial_to_final_klemmung_ratio": self.initial_to_final_klemmung_ratio,
            "volumetric_efficiency": self.volumetric_efficiency,
            "max_mass_flux": self.max_mass_flux,
        }

    def _report_body(self, file: IO) -> None:
        print("\nBURN REGRESSION", file=file)
        if self.propellant_mass[0] > 1:
            print(
                f" Propellant initial mass {self.propellant_mass[0]:.3f} kg", file=file
            )
        else:
            print(
                f" Propellant initial mass {self.propellant_mass[0] * 1e3:.3f} g",
                file=file,
            )
        print(" Mean Kn: %.2f" % np.mean(self.klemmung), file=file)
        print(" Max Kn: %.2f" % np.max(self.klemmung), file=file)
        print(
            f" Initial to final Kn ratio: {self.initial_to_final_klemmung_ratio:.3f}",
            file=file,
        )
        print(f" Volumetric efficiency: {self.volumetric_efficiency:.3%}", file=file)
        print(" Burn profile: " + self.burn_profile, file=file)
        print(
            f" Max initial mass flux: {self.max_mass_flux:.3f} kg/s-m-m or "
            f"{conversions.convert_mass_flux_metric_to_imperial(self.max_mass_flux):.3f} "
            "lb/s-in-in",
            file=file,
        )

        print("\nCHAMBER PRESSURE", file=file)
        print(
            f" Maximum, average chamber pressure: {np.max(self.chamber_pressure) * 1e-6:.3f}, "
            f"{np.mean(self.chamber_pressure) * 1e-6:.3f} MPa",
            file=file,
        )

        print("\nTHRUST AND IMPULSE", file=file)
        print(
            f" Maximum, average thrust: {np.max(self.thrust):.3f}, {np.mean(self.thrust):.3f} N",
            file=file,
        )
        print(
            f" Total, specific impulses: {self.total_impulse:.3f} N-s, {self.specific_impulse:.3f} s",
            file=file,
        )
        print(
            f" Burnout time, thrust time: {self.burn_time:.3f}, {self.thrust_time:.3f} s",
            file=file,
        )

        print("\nNOZZLE DESIGN", file=file)
        print(
            f" Average nozzle efficiency: {np.mean(self.nozzle_efficiency):.3%}",
            file=file,
        )
        print(
            f" Average overall efficiency: {np.mean(self.overall_efficiency):.3%}",
            file=file,
        )
        print(
            f" Divergent nozzle loss fraction: {np.mean(self.divergent_loss):.3%}",
            file=file,
        )
        print(
            f" Average kinetics loss fraction: {np.mean(self.kinetics_loss):.3%}",
            file=file,
        )
        print(
            f" Average boundary layer loss fraction: {np.mean(self.boundary_layer_loss):.3%}",
            file=file,
        )
        print(
            f" Average two-phase flow loss fraction: {np.mean(self.two_phase_loss):.3%}",
            file=file,
        )
