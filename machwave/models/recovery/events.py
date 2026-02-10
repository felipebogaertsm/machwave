from abc import ABC, abstractmethod

import numpy as np

from machwave.models.recovery.parachutes import Parachute


class RecoveryEvent(ABC):
    def __init__(self, trigger_value: float, parachute: Parachute) -> None:
        """Initialize a RecoveryEvent object.

        Args:
            trigger_value: Trigger value for the event.
            parachute: Parachute associated with the event.
        """
        self.trigger_value = trigger_value
        self.parachute = parachute

    @abstractmethod
    def is_active(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: np.ndarray,
    ) -> bool:
        """Check if the recovery event is active.

        Args:
            height: Array of heights.
            time: Array of time values.
            velocity: Array of velocities.
            propellant_mass: Array of propellant masses.

        Returns:
            True if the recovery event is active, False otherwise.
        """
        return False


class AltitudeBasedEvent(RecoveryEvent):
    def is_active(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: np.ndarray,
    ) -> bool:
        """Check if the altitude-based recovery event is active.

        The event is considered active if the current velocity is negative
        (descending) and the current height is below the trigger value.

        Args:
            height: Array of heights.
            time: Array of time values.
            velocity: Array of velocities.
            propellant_mass: Array of propellant masses.

        Returns:
            True if altitude-based recovery event is active, False otherwise.
        """
        if velocity[-1] < 0 and height[-1] < self.trigger_value:
            return True
        else:
            return False


class ApogeeBasedEvent(RecoveryEvent):
    def __init__(self, trigger_value: float, parachute: Parachute) -> None:
        """Initialize an ApogeeBasedEvent object.

        Args:
            trigger_value: Trigger value for the event.
            parachute: Parachute associated with the event.
        """
        super().__init__(trigger_value, parachute)

    def is_active(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: np.ndarray,
    ) -> bool:
        """Check if the apogee-based recovery event is active.

        The event is considered active if the current velocity is negative
        (descending), the propellant mass is zero (indicating the propellant
        is depleted), and the time since apogee is greater than or equal to
        the trigger value.

        Args:
            height: Array of heights.
            time: Array of time values.
            velocity: Array of velocities.
            propellant_mass: Array of propellant masses.

        Returns:
            True if apogee-based recovery event is active, False otherwise.
        """
        max_height_index = np.argmax(height)
        apogee_time = time[max_height_index]

        if (
            propellant_mass == 0  # Propellant is depleted
            and velocity[-1] < 0  # Descending velocity
            and time[-1] >= self.trigger_value + apogee_time  # Time condition
        ):
            return True
        else:
            return False
