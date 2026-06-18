from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import numpy as np

import machwave.core.compressible_flow.nozzle as nozzle_core
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
            nozzle_loss_model: Nozzle thrust-coefficient loss model. Motor
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

    @abstractmethod
    def get_launch_mass(self) -> float:
        """Return the total mass of the motor before launch [kg]."""
        pass

    @abstractmethod
    def get_dry_mass(self) -> float:
        """Return the dry mass of the motor [kg]."""
        pass

    @abstractmethod
    def get_center_of_gravity(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        """
        Return the center of gravity of the propulsion system.

        The coordinate system origin corresponds to the combustion chamber axis
        at the nozzle exit plane, with positive x pointing toward the bulkhead.

        Returns:
            1D array of shape `(3,)` containing the `[x, y, z]` coordinates of
            the center of gravity [m].
        """
        pass

    @property
    @abstractmethod
    def initial_propellant_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        pass

    def get_thrust(self, cf: float, chamber_pressure: float) -> float:
        """
        Return the instantaneous thrust [N].

        Uses the nozzle throat area from the thrust chamber.

        Args:
            cf: Instantaneous thrust coefficient (dimensionless).
            chamber_pressure: Instantaneous chamber pressure [Pa].

        Returns:
            Instantaneous thrust [N].
        """
        return nozzle_core.get_thrust_from_thrust_coefficient(
            cf,
            chamber_pressure,
            self.thrust_chamber.nozzle.get_throat_area(),
        )
