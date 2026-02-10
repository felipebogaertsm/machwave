import numpy as np

from machwave.core.geometric import get_circle_area


class DragCoefficientTypeError(Exception):
    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


class Fuselage:
    """Deals primarily with aerodynamic parameters."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        drag_coefficient: np.ndarray | float | int,
        frontal_area: float | None = None,
    ) -> None:
        """Initialize the Fuselage object.

        Args:
            length: Fuselage length [m].
            outer_diameter: Fuselage outer diameter [m].
            drag_coefficient: Drag coefficient value(s). Can be single value,
                or 2D array with first column as velocity and second column
                as corresponding drag coefficient.
        """
        self.length = length
        self.outer_diameter = outer_diameter
        self._frontal_area = frontal_area
        self._drag_coefficient = drag_coefficient

    @property
    def frontal_area(self) -> float:
        """Frontal area of the fuselage [m^2]."""
        if self._frontal_area is not None:
            return self._frontal_area

        return get_circle_area(self.outer_diameter)

    def get_drag_coefficient(self, velocity: float = 0) -> float:
        """Get the drag coefficient of the fuselage.

        Args:
            velocity: Velocity at which to calculate drag coefficient.

        Returns:
            Drag coefficient value.

        Raises:
            DragCoefficientTypeError: If type of drag_coefficient is not
                recognized.
            ValueError: If velocity is None and drag_coefficient is a list.
        """
        if isinstance(self._drag_coefficient, np.ndarray):
            if velocity is None:
                raise ValueError(
                    "`velocity` must be provided when `drag_coefficient` is a list."
                )

            return np.interp(
                velocity,
                self._drag_coefficient[:, 0],
                self._drag_coefficient[:, 1],
            )

        elif isinstance(self._drag_coefficient, (float, int)):
            return self._drag_coefficient
        else:
            raise DragCoefficientTypeError(
                self._drag_coefficient,
                "Type not recognized in 'drag_coefficient'. "
                "Must be a float, int, or a numpy array",
            )
