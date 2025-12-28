from abc import ABC
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d

from machwave.core.mathematics.geometric import (
    get_circle_area,
    get_contours,
    get_length,
)
from machwave.models.propulsion.grain import GrainGeometryError, GrainSegment3D

from .base import FMMGrainSegment


class FMMGrainSegment3D(FMMGrainSegment, GrainSegment3D, ABC):
    """
    Fast Marching Method (FMM) implementation for 3D grain segment.

    This class was inspired by the Andrew Reilley's software openMotor, in
    particular the fmm module.
    openMotor's repository can be accessed at:
    https://github.com/reilleya/openMotor
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        spacing: float,
        inhibited_ends: int = 0,
        map_dim: int = 100,
        density_ratio: float = 1.0,
    ) -> None:
        self.burn_area_interp_func: Callable[[float], float] | None = None
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
            density_ratio=density_ratio,
        )

    def get_port_area(self, web_distance: float, z: float) -> float:
        """
        Calculates the port area at a given web distance and axial height z.

        This method extracts a single 2D slice from the 3D face map by converting
        the physical height z into an integer index, and then computes the port
        area for that slice.

        Args:
            web_distance: The distance traveled into the grain web.
            z: Axial position (in meters) along the grain, where z=0 is the top
                and z=self.length is the bottom (or vice versa, depending on
                geometry setup).

        Returns:
            A float representing the port area at the specified z slice, in m².
        """
        map_dist = self.normalize(web_distance)
        valid = np.logical_not(self.get_mask())
        solid = np.logical_and(self.get_regression_map() > map_dist, valid)

        normalized_z = z / self.length
        max_index = self.get_normalized_length() - 1
        z_index = int(round(normalized_z * max_index))
        z_index = 0 if z_index < 0 else (max_index if z_index > max_index else z_index)

        face_area = self.map_to_area(float(np.count_nonzero(solid[z_index])))
        return get_circle_area(self.outer_diameter) - face_area

    def get_normalized_length(self) -> int:
        return int(self.map_dim * self.length / self.outer_diameter)

    def get_maps(
        self,
    ) -> tuple[
        NDArray[np.float64],
        NDArray[np.float64],
        NDArray[np.float64],
    ]:
        if self.maps is None:
            map_y, map_z, map_x = np.meshgrid(
                np.linspace(-1, 1, self.map_dim),
                np.linspace(1, 0, self.get_normalized_length()),  # z axis
                np.linspace(-1, 1, self.map_dim),
            )

            self.maps = (map_x, map_y, map_z)

        return self.maps

    def get_mask(self) -> NDArray[np.bool_]:
        if self.mask is None:
            map_x, map_y, _ = self.get_maps()
            self.mask = (map_x**2 + map_y**2) > 1

        return self.mask

    def get_contours(
        self, web_distance: float, length_normalized: float
    ) -> list[NDArray[np.float64]]:
        map_dist = self.normalize(web_distance)
        valid = np.logical_not(self.get_mask())
        boolean_3d = np.logical_and(self.get_regression_map() > map_dist, valid)

        z_index = int(round(length_normalized))
        boolean_slice_2d = boolean_3d[z_index]

        return get_contours(
            boolean_slice_2d,
            map_dist,
        )

    def _get_burn_area_uncached(self, *, map_dist: float) -> float:
        valid = np.logical_not(self.get_mask())
        boolean_3d = np.logical_and(self.get_regression_map() > map_dist, valid)

        web_distance = self.denormalize(map_dist)
        length_factor = self.get_length(web_distance=web_distance) / self.map_dim

        total = 0.0
        for z_index in range(self.get_normalized_length()):
            boolean_slice_2d = boolean_3d[z_index]
            contours = get_contours(boolean_slice_2d, map_dist)
            perimeter = sum(
                self.map_to_length(get_length(contour, self.map_dim))
                for contour in contours
            )
            total += float(perimeter) * float(length_factor)

        return float(total)

    def get_burn_area_interp_func(self) -> Callable[[float], float]:
        """Return a cached interpolator for burn area [m^2] vs normalized web."""

        if self.burn_area_interp_func is None:
            regression_map = self.get_regression_map()
            valid = np.logical_not(self.get_mask())

            values = np.asarray(regression_map[valid], dtype=np.float64).ravel()
            if values.size == 0:
                self.burn_area_interp_func = interp1d(
                    np.asarray([0.0], dtype=np.float64),
                    np.asarray([0.0], dtype=np.float64),
                    bounds_error=False,
                    fill_value=(0.0, 0.0),
                    assume_sorted=True,
                )
                return self.burn_area_interp_func

            values.sort()
            max_dist = float(values[-1])
            oversample = 3
            denom = float(self.map_dim * oversample)
            step_count = int(max_dist * denom) + 2
            distances = np.arange(step_count, dtype=np.float64) / denom

            burn_area_values = np.empty_like(distances, dtype=np.float64)
            for i, dist in enumerate(distances):
                burn_area_values[i] = self._get_burn_area_uncached(map_dist=float(dist))

            burn_area_values = np.asarray(burn_area_values, dtype=np.float64)
            self.burn_area_interp_func = interp1d(
                distances,
                burn_area_values,
                bounds_error=False,
                fill_value=(float(burn_area_values[0]), float(burn_area_values[-1])),
                assume_sorted=True,
            )

        return self.burn_area_interp_func

    def get_burn_area(self, web_distance: float) -> float:
        if web_distance > self.get_web_thickness():
            return 0.0
        map_distance = self.normalize(web_distance)
        value = float(self.get_burn_area_interp_func()(map_distance))
        return max(0.0, value)

    def get_volume_per_element(self) -> float:
        return (self.denormalize(self.get_cell_size()) * 2) ** 3

    def get_volume(self, web_distance: float) -> float:
        face_map = self.get_face_map(web_distance=web_distance)
        active_elements = np.count_nonzero(face_map == 1)
        volume_per_element = self.get_volume_per_element()
        return active_elements * volume_per_element

    def get_center_of_gravity(self, web_distance: float) -> NDArray[np.float64]:
        """
        Calculates the center of gravity of a 3D grain segment in 3D space
        at a specific web distance.

        Raises:
            GrainGeometryError: If the web distance traveled is greater than
                the grain segment's web thickness.
        """
        if web_distance > self.get_web_thickness():
            raise GrainGeometryError(
                "The web distance traveled is greater than the grain "
                "segment's web thickness."
            )

        # Get the 2D face map at the given web distance
        face_map = self.get_face_map(web_distance)

        # Mask the regions where the face map has active material (equal to 1)
        mask = face_map == 1

        # Get the non-masked elements
        z_indices, y_indices, x_indices = np.where(mask)

        # Point of reference is segment's top center
        center_shift = self.map_dim / 2
        x_coords = x_indices - center_shift
        y_coords = y_indices - center_shift
        z_coords = z_indices  # Already 0-based

        # Calculate the normalized center of gravity
        x_cog_normalized = np.mean(x_coords)
        y_cog_normalized = np.mean(y_coords)
        z_cog_normalized = np.mean(z_coords)

        # Convert normalized coordinates into physical meters
        x_cog = self.map_to_length(x_cog_normalized)
        y_cog = self.map_to_length(y_cog_normalized)
        z_cog = self.map_to_length(z_cog_normalized)

        return np.array([x_cog, y_cog, z_cog], dtype=np.float64)
