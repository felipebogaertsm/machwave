from abc import ABC

import numpy as np
from numpy.typing import NDArray

from machwave.models.propulsion.grain import GrainGeometryError, GrainSegment3D
from machwave.services.math.geometric import (
    get_circle_area,
    get_contours,
    get_length,
)

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
    ) -> None:
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            spacing=spacing,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
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
        face_map_3d = self.get_face_map(web_distance=web_distance)  # 3D face map

        normalized_z = z / self.length
        max_index = self.get_normalized_length() - 1  # last valid slice index
        z_index = int(round(normalized_z * max_index))

        if z_index < 0:
            z_index = 0
        elif z_index > max_index:
            z_index = max_index

        face_map_slice = face_map_3d[z_index]
        face_area = self.map_to_area(np.count_nonzero(face_map_slice == 1))
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

    def get_mask(self) -> np.ndarray:
        if self.mask is None:
            map_x, map_y, _ = self.get_maps()
            self.mask = (map_x**2 + map_y**2) > 1

        return self.mask

    def get_contours(
        self, web_distance: float, length_normalized: float
    ) -> list[np.typing.NDArray[np.float64]]:
        map_dist = self.normalize(web_distance)
        valid = np.logical_not(self.get_mask())
        boolean_3d = np.logical_and(self.get_regression_map() > map_dist, valid)

        z_index = int(round(length_normalized))
        boolean_slice_2d = boolean_3d[z_index]

        return get_contours(
            boolean_slice_2d,
            map_dist,
        )

    def get_burn_area(self, web_distance: float) -> float:
        """
        NOTE 1: Still needs to be validated.
        NOTE 2: Refactor to use only numpy arrays.
        """
        if web_distance > self.get_web_thickness():
            return 0

        burn_area_array = np.array([])

        for i in range(self.get_normalized_length()):
            contours = self.get_contours(web_distance=web_distance, length_normalized=i)
            perimeter = np.sum(
                [
                    self.map_to_length(get_length(contour, self.map_dim))
                    for contour in contours
                ]
            )

            burn_area_array = np.append(
                burn_area_array,
                perimeter * self.get_length(web_distance=web_distance) / self.map_dim,
            )

        return np.sum(burn_area_array)

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
