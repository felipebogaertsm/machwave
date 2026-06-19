from __future__ import annotations

import dataclasses
import functools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeAlias

import machwave.core.conversions as conversions
import machwave.models.motors as motors

if TYPE_CHECKING:
    import machwave.models.propellants as propellants
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
class TimestepConditions(ABC):
    """
    Engine conditions at one simulation timestep.

    Holds the scalar operating quantities every engine type computes for the
    step, minus the performance outputs derived from them (thrust, thrust
    coefficient, nozzle efficiency). A nozzle loss component reads whatever it
    needs from here. Each engine type provides its own concrete subclass.
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

    @property
    @abstractmethod
    def mixture_type(self) -> propellants.MixtureType:
        """Engine mixture type these conditions describe."""

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
