import numpy as np

from machwave.models.recovery.events import RecoveryEvent


class Recovery:
    def __init__(self) -> None:
        """
        Initializes a Recovery object.
        """
        self.events = []

    def add_event(self, recovery_event: RecoveryEvent) -> None:
        """Add a recovery event to the list of events.

        Args:
            recovery_event: Recovery event to add.
        """
        self.events.append(recovery_event)

    def get_drag_coefficient_and_area(
        self,
        height: np.ndarray,
        time: np.ndarray,
        velocity: np.ndarray,
        propellant_mass: float,
    ) -> tuple[float, float]:
        """Calculate cumulative drag coefficient and area for active events.

        We first filter the self.events list to include only the active
        events based on the provided conditions. Then, we calculate the
        cumulative drag coefficient and area directly from the filtered list
        using list comprehension and the sum function.

        Args:
            height: Array of heights.
            time: Array of time values.
            velocity: Array of velocities.
            propellant_mass: Instant propellant mass.

        Returns:
            Cumulative drag coefficient and area.
        """
        active_events = [
            event
            for event in self.events
            if event.is_active(height, time, velocity, propellant_mass)
        ]

        drag_coefficient = sum(
            event.parachute.drag_coefficient for event in active_events
        )
        area = sum(event.parachute.area for event in active_events)

        return drag_coefficient, area
