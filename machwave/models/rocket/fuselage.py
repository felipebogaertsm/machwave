import numpy as np

from machwave.services.math.geometric import get_circle_area


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
        """
        Initialize the Fuselage object.

        Args:
            length (float): Length of the fuselage.
            outer_diameter (float): Outer diameter of the fuselage.
            drag_coefficient (np.ndarray | float | int): Drag coefficient value(s).
                It can be a single value, or a 2D array with the first column being velocity
                and the second column being the corresponding drag coefficient.

        Returns:
            None
        """
        self.length = length
        self.outer_diameter = outer_diameter
        self._frontal_area = frontal_area
        self._drag_coefficient = drag_coefficient

    @property
    def frontal_area(self) -> float:
        """
        Frontal area of the fuselage.

        Returns:
            float: Frontal area in square meters.
        """
        if self._frontal_area is not None:
            return self._frontal_area

        return get_circle_area(self.outer_diameter)

    def get_drag_coefficient(self, velocity: float = 0) -> float:
        """Get the drag coefficient of the fuselage.

        Args:
            velocity (float, optional): Velocity at which to calculate the
                drag coefficient. If not provided, the default value is None.

        Returns:
            float: Drag coefficient value.

        Raises:
            DragCoefficientTypeError: If the type of `drag_coefficient` is
                not recognized.
            ValueError: If `velocity` is None and `drag_coefficient` is a list.

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
