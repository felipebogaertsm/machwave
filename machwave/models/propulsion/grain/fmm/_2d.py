from abc import ABC
from typing import Callable, Optional

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from machwave.models.propulsion.grain import GrainGeometryError, GrainSegment2D
from machwave.services.math.geometric import (
    get_circle_area,
    get_contours,
    get_length,
)

from .base import FMMGrainSegment


class FMMGrainSegment2D(FMMGrainSegment, GrainSegment2D, ABC):
    """
    Fast Marching Method (FMM) implementation for 2D grain segment.

    This class was inspired by Andrew Reilley's openMotor software,
    in particular the fmm module. See:
    https://github.com/reilleya/openMotor
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: int = 0,
        map_dim: int = 1000,
    ) -> None:
        self.face_area_interp_func: Optional[Callable[[float], float]] = None
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
        )

    def get_maps(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Return a tuple of two 2D arrays (map_x, map_y).
        Each is of shape (map_dim, map_dim), ranging from -1 to 1.
        """
        if self.maps is None:
            map_x, map_y = np.meshgrid(
                np.linspace(-1, 1, self.map_dim, dtype=np.float64),
                np.linspace(-1, 1, self.map_dim, dtype=np.float64),
            )
            self.maps = (map_x, map_y)
        return self.maps

    def get_mask(self) -> NDArray[np.bool]:
        """
        Return a boolean mask indicating which points lie outside the unit circle.
        """
        if self.mask is None:
            map_x, map_y = self.get_maps()
            self.mask = (map_x**2 + map_y**2) > 1
        return self.mask

    def get_contours(self, web_distance: float) -> list[NDArray[np.float64]]:
        """
        Return a list of contour arrays for the given web distance.
        Each contour is typically an (N,2) array of (row, col) points.
        """
        map_dist = self.normalize(web_distance)
        # get_contours is imported from machwave.services.math.geometric
        return get_contours(self.get_regression_map(), map_dist)

    def get_port_area(self, web_distance: float) -> float:
        """
        Return the grain's port area (open cross-sectional area) at the given web distance.
        Could be a scalar or array, depending on how the computations are done.
        """
        face_area = self.get_face_area(web_distance)
        return get_circle_area(self.outer_diameter) - face_area

    def get_face_area_interp_func(self) -> Callable[[float], float]:
        """
        Build and return an interpolation function that, given a normalized
        web distance, returns the face area in square meters.
        """
        if self.face_area_interp_func is None:
            regression_map = self.get_regression_map()
            max_dist = np.amax(regression_map)

            face_area_values = []
            distances = []
            valid = np.logical_not(self.get_mask())

            # Compute face area vs. distance in discrete steps
            for i in range(int(max_dist * self.map_dim) + 2):
                dist = i / self.map_dim
                distances.append(dist)

                # Count how many pixels remain above 'dist'
                count = np.count_nonzero(np.logical_and(regression_map > dist, valid))
                area = self.map_to_area(count)
                face_area_values.append(area)

            # Smooth and interpolate
            smoothed = savgol_filter(face_area_values, 31, 5)
            self.face_area_interp_func = interp1d(distances, smoothed)

        return self.face_area_interp_func

    def get_face_area(self, web_distance: float) -> float:
        """
        Return the face area at the given web distance.
        """
        map_distance = self.normalize(web_distance)
        return float(self.get_face_area_interp_func()(map_distance))

    def get_core_perimeter(self, web_distance: float) -> float:
        """
        Return the perimeter of the open core at the given web distance.
        """
        contours = self.get_contours(web_distance)
        # Sum the lengths of all contour segments
        return sum(
            self.map_to_length(get_length(contour, self.map_dim))
            for contour in contours
        )

    def get_core_area(self, web_distance: float) -> float:
        """
        Calculate the core (internal) area at the given web distance by
        multiplying perimeter by grain segment length (a 2D approximation).
        """
        return self.get_core_perimeter(web_distance) * self.get_length(web_distance)

    def get_center_of_gravity(self, web_distance: float) -> NDArray[np.float64]:
        """
        Return the center of gravity of the 2D grain segment at a specific web distance.

        Raises:
            GrainGeometryError: If web distance exceeds the web thickness, or if no active material is found.
        """
        if web_distance > self.get_web_thickness():
            raise GrainGeometryError(
                "The web distance traveled is greater than the grain segment's web thickness."
            )

        face_map = self.get_face_map(web_distance)
        mask = face_map == 1  # active material only

        y_indices, x_indices = np.where(mask)
        if len(x_indices) == 0 or len(y_indices) == 0:
            raise GrainGeometryError(
                "No active material found at the given web distance."
            )

        center_shift = self.map_dim / 2
        x_coords = x_indices - center_shift
        y_coords = y_indices - center_shift

        x_cog_normalized = np.mean(x_coords)
        y_cog_normalized = np.mean(y_coords)

        x_cog = self.map_to_length(x_cog_normalized)
        y_cog = self.map_to_length(y_cog_normalized)
        z_cog = self.length / 2

        # Return as a float64 NumPy array
        return np.array([x_cog, y_cog, z_cog], dtype=np.float64)
