from __future__ import annotations

import dataclasses
import functools

import machwave.core.conversions as conversions
import machwave.models.propellants.properties as propellant_properties_models
import machwave.models.thrust_chamber as thrust_chamber_models


@dataclasses.dataclass(frozen=True, kw_only=True)
class NozzleLossEvaluationContext:
    """
    Parameters that a nozzle loss component may need to evaluate the losses.

    Each timestep of a motor simulation must have a context object, since chamber
    pressure, propellant properties, and other parameters change over time.
    """

    time: float
    chamber_pressure: float
    nozzle: thrust_chamber_models.Nozzle
    propellant_properties: propellant_properties_models.ThermochemicalProperties
    free_chamber_volume: float

    @functools.cached_property
    def chamber_pressure_psi(self) -> float:
        """Chamber pressure [psi]."""
        return conversions.convert_pa_to_psi(self.chamber_pressure)

    @functools.cached_property
    def throat_diameter_inch(self) -> float:
        """Nozzle throat diameter [in]."""
        return conversions.convert_meter_to_inch(self.nozzle.throat_diameter)

    @functools.cached_property
    def characteristic_length_inch(self) -> float:
        """Chamber characteristic length [in]."""
        return conversions.convert_meter_to_inch(
            self.free_chamber_volume / self.nozzle.get_throat_area()
        )
