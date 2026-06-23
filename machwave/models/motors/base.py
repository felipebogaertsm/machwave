from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants as propellants
import machwave.models.thrust_chamber as thrust_chamber_models

P = TypeVar("P", bound=propellants.Propellant)
T = TypeVar("T", bound=thrust_chamber_models.ThrustChamber)


class Motor(Generic[P, T], ABC):
    """Abstract rocket motor/engine for solid, hybrid, or biliquid systems."""

    def __init__(
        self,
        propellant: P,
        thrust_chamber: T,
        combustion_efficiency: float = 0.95,
        nozzle_loss_model: nozzle_losses.NozzleLossModel | None = None,
    ) -> None:
        """
        Initialize attributes common to any motor or engine.

        Args:
            propellant: Propellant used in the motor.
            thrust_chamber: Thrust chamber of the motor.
            combustion_efficiency: Ratio of the actual flame temperature to the ideal
                adiabatic flame temperature (0, 1].
            nozzle_loss_model: Nozzle thrust coefficient loss model. Motor
                subclasses supply an engine-appropriate default.

        Raises:
            ValueError: If `combustion_efficiency` is not in (0, 1], if
                `nozzle_loss_model` is missing, or if its mixture type does not
                match the propellant.
        """
        if not 0.0 < combustion_efficiency <= 1.0:
            raise ValueError(
                "combustion_efficiency must be in the range (0, 1], got "
                f"{combustion_efficiency}"
            )

        if nozzle_loss_model is None:
            raise ValueError(
                "nozzle_loss_model must be provided; motor subclasses supply a default."
            )

        if nozzle_loss_model.mixture_type != propellant.mixture_type:
            raise ValueError(
                "nozzle_loss_model mixture type "
                f"{nozzle_loss_model.mixture_type} does not match propellant "
                f"mixture type {propellant.mixture_type}."
            )

        self.propellant = propellant
        self.thrust_chamber = thrust_chamber
        self.combustion_efficiency = combustion_efficiency
        self.nozzle_loss_model = nozzle_loss_model

    @property
    @abstractmethod
    def initial_propellant_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        pass
