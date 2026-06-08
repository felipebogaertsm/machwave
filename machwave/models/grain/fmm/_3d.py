from abc import ABC
from collections.abc import Callable

import numpy as np
import skfmm
from numpy.typing import NDArray
from scipy.interpolate import interp1d
from skimage import measure

import machwave.core.filters as filters
import machwave.core.geometric as geometric
import machwave.core.mechanics as mechanics
import machwave.models.grain as grain
import machwave.models.grain.base as grain_base

from . import base as fmm_base
from . import contours as fmm_contours


class FMMGrainSegment3D(fmm_base.FMMGrainSegment, grain.GrainSegment3D, ABC):
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
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        map_dim: int = 100,
        density_ratio: float = 1.0,
    ) -> None:
        self.burn_area_interp_func: Callable[[float], float] | None = None
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            map_dim=map_dim,
            density_ratio=density_ratio,
        )

    def get_port_area(self, web_distance: float, z: float = 0.0) -> float:
        """
        Calculates the port area at a given web distance and axial height z.

        This method extracts a single 2D slice from the 3D face map by converting
        the physical height z into an integer index, and then computes the port
        area for that slice.

        Args:
            web_distance: The distance traveled into the grain web.
            z: Axial position along the grain [m], measured from the aft
                (nozzle) end. Defaults to nozzle end.

        Returns:
            A float representing the port area at the specified z slice, in m^2.
        """
        map_dist = self.normalize(web_distance)
        valid = np.logical_not(self.get_mask())
        solid = np.logical_and(self.get_regression_map() > map_dist, valid)

        normalized_z = z / self.length
        max_index = self.get_normalized_length() - 1
        z_index = int(round(normalized_z * max_index))
        z_index = 0 if z_index < 0 else (max_index if z_index > max_index else z_index)

        face_area = float(self.map_to_area(float(np.count_nonzero(solid[z_index]))))
        return geometric.get_circle_area(self.outer_diameter) - face_area

    def get_normalized_length(self) -> int:
        return int(self.map_dim * self.length / self.outer_diameter)

    def validate(self) -> None:
        super().validate()
        self._validate_normalized_length()

    def _validate_normalized_length(self) -> None:
        # < 3 slices: get_port_area indexes a size-0 axis and inhibition is skipped
        normalized_length = self.get_normalized_length()
        if normalized_length < 3:
            raise grain.GrainGeometryError(
                f"Normalized axial length must be at least 3, got "
                f"{normalized_length}; increase map_dim or the "
                f"length-to-outer-diameter ratio."
            )

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

    def _apply_inhibition(
        self,
        face_map: NDArray[np.int_],
        outside: NDArray[np.bool_],
    ) -> tuple[NDArray[np.int_], NDArray[np.bool_]]:
        if face_map.shape[0] <= 2:
            return face_map, outside

        bore_mask = np.zeros_like(face_map, dtype=bool)
        bore_mask[1:-1] = face_map[1:-1] == 0
        bore_mask[0] = bore_mask[1]
        bore_mask[-1] = bore_mask[-2]

        # super() runs binary_erosion on the full 3D volume, which includes the
        # end-face layers in the boundary_ring. Apply end inhibition AFTER so
        # those cells are not overwritten back to 0 by the outer-surface logic.
        face_map, outside = super()._apply_inhibition(face_map, outside)

        if self.inhibited_surfaces.upper_end:
            end_face_zeros = (face_map[-1] == 0) & ~bore_mask[-1]
            face_map[-1][end_face_zeros] = 1

        if self.inhibited_surfaces.lower_end:
            end_face_zeros = (face_map[0] == 0) & ~bore_mask[0]
            face_map[0][end_face_zeros] = 1

        if self.inhibited_surfaces.inner_surface:
            outside = outside | bore_mask

        return face_map, outside

    def _regression_distance(self, masked_face: np.ndarray) -> np.ndarray:
        # Regression speed needs to be calibrated for the z axes separately from the x
        # and y axes, because the 3D grid is anisotropic
        axial_pitch = self.length / max(self.get_normalized_length() - 1, 1)
        radial_pitch = self.outer_diameter / (self.map_dim - 1)
        distance = skfmm.distance(
            masked_face,
            dx=[axial_pitch, radial_pitch, radial_pitch],  # type: ignore[arg-type]
        )
        return distance * (2.0 / self.outer_diameter)

    def get_contours(
        self, web_distance: float, length_normalized: float
    ) -> list[NDArray[np.float64]]:
        map_dist = self.normalize(web_distance)
        z_index = int(round(length_normalized))
        regression_slice = self.get_regression_map()[z_index]
        return fmm_contours.get_contours(regression_slice, map_dist)

    @staticmethod
    def _measure_iso_surface_area(
        regression_field: NDArray[np.float64],
        level: float,
        voxel_spacing: tuple[float, float, float],
    ) -> float:
        """Marching-cubes area [m^2] of one regression iso-level, 0 if empty."""
        try:
            vertices, faces, _, _ = measure.marching_cubes(
                regression_field, level=level, spacing=voxel_spacing
            )
        except (ValueError, RuntimeError):
            return 0.0
        return float(measure.mesh_surface_area(vertices, faces))

    def get_burn_area_interp_func(self) -> Callable[[float], float]:
        """Return a cached interpolator for burn area [m^2] vs web distance [m]."""
        if self.burn_area_interp_func is None:
            regression_map = self.get_regression_map()
            regression_values = np.asarray(
                regression_map[~np.ma.getmaskarray(regression_map)], dtype=np.float64
            )
            max_level = (
                float(regression_values.max()) if regression_values.size else 0.0
            )
            if max_level <= 0.0:
                self.burn_area_interp_func = interp1d(
                    np.asarray([0.0], dtype=np.float64),
                    np.asarray([0.0], dtype=np.float64),
                    bounds_error=False,
                    fill_value=0.0,
                    assume_sorted=True,
                )
                return self.burn_area_interp_func

            # Lift the inhibited casing above every iso level so marching cubes
            # meshes only the burning front, not the wall.
            regression_field = np.ma.filled(regression_map, max_level + 1.0)
            axial_spacing = self.length / max(self.get_normalized_length() - 1, 1)
            radial_spacing = self.outer_diameter / (self.map_dim - 1)
            voxel_spacing = (axial_spacing, radial_spacing, radial_spacing)

            # The iso-surface at level 0 lies on the voxelized initial face and is
            # degenerate, so sample above it and hold the first area back to web 0.
            sample_count = 80
            levels = np.linspace(max_level / sample_count, max_level, sample_count)
            surface_areas = np.array(
                [
                    self._measure_iso_surface_area(
                        regression_field, float(level), voxel_spacing
                    )
                    for level in levels
                ],
                dtype=np.float64,
            )
            web_distances = np.concatenate(
                ([0.0], np.asarray(self.denormalize(levels), dtype=np.float64))
            )
            surface_areas = np.concatenate(([surface_areas[0]], surface_areas))

            smoothed_areas = filters.smooth_savitzky_golay(
                surface_areas, window_length=9, polyorder=3
            )
            self.burn_area_interp_func = interp1d(
                web_distances,
                smoothed_areas,
                bounds_error=False,
                fill_value=(
                    float(smoothed_areas[0]),
                    float(smoothed_areas[-1]),
                ),  # type: ignore[arg-type]
                assume_sorted=True,
            )

        return self.burn_area_interp_func

    def get_burn_area(self, web_distance: float) -> float:
        if web_distance > self.get_web_thickness():
            return 0.0
        return max(0.0, float(self.get_burn_area_interp_func()(web_distance)))

    def get_volume_per_element(self) -> float:
        return (float(self.denormalize(self.get_cell_size())) * 2) ** 3

    def get_volume(self, web_distance: float) -> float:
        face_map = self.get_face_map(web_distance=web_distance)
        active_elements = np.count_nonzero(face_map == 1)
        volume_per_element = self.get_volume_per_element()
        return active_elements * volume_per_element

    def _validate_web_distance(self, web_distance: float) -> None:
        """
        Validate that web distance does not exceed web thickness.

        Raises:
            GrainGeometryError: If web distance exceeds web thickness.
        """
        if web_distance > self.get_web_thickness():
            raise grain.GrainGeometryError(
                "The web distance traveled is greater than the grain "
                "segment's web thickness."
            )

    def _get_active_material_indices(
        self, web_distance: float
    ) -> tuple[NDArray[np.int_], NDArray[np.int_], NDArray[np.int_]]:
        """
        Get indices of active material at given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Tuple of (z_indices, y_indices, x_indices) for active material.

        Raises:
            GrainGeometryError: If no active material is found.
        """
        face_map = self.get_face_map(web_distance)
        mask = face_map == 1  # active material only
        z_indices, y_indices, x_indices = np.where(mask)

        if len(x_indices) == 0:
            raise grain.GrainGeometryError(
                "No active material found at the given web distance."
            )

        return z_indices, y_indices, x_indices

    def _indices_to_normalized_coords(
        self,
        z_indices: NDArray[np.int_],
        y_indices: NDArray[np.int_],
        x_indices: NDArray[np.int_],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """
        Convert indices to normalized coordinates centered at origin.

        Args:
            z_indices: Z-axis (axial) indices from face map.
            y_indices: Y-axis indices from face map.
            x_indices: X-axis indices from face map.

        Returns:
            Tuple of (x_coords, y_coords, z_coords) in normalized units.
        """
        center_shift = self.map_dim / 2
        x_coords = (x_indices - center_shift).astype(np.float64)
        y_coords = (y_indices - center_shift).astype(np.float64)
        z_coords = z_indices.astype(np.float64)
        return x_coords, y_coords, z_coords

    def get_center_of_gravity(self, web_distance: float) -> NDArray[np.float64]:
        """
        Return the center of gravity of a 3D FMM grain segment.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Center of gravity [z, x, y] in meters from the port of the segment.

        Raises:
            GrainGeometryError: If web distance exceeds the web thickness, or
                if no active material is found.
        """
        self._validate_web_distance(web_distance)
        z_indices, y_indices, x_indices = self._get_active_material_indices(
            web_distance
        )
        x_coords, y_coords, z_coords = self._indices_to_normalized_coords(
            z_indices, y_indices, x_indices
        )

        # Convert normalized coordinates into physical meters
        x_phys = np.asarray(self.map_to_length(x_coords), dtype=np.float64)
        y_phys = np.asarray(self.map_to_length(y_coords), dtype=np.float64)
        z_phys = np.asarray(self.map_to_length(z_coords), dtype=np.float64)

        return mechanics.get_center_of_gravity(x_phys, y_phys, z_phys)

    def get_moment_of_inertia(
        self, ideal_density: float, web_distance: float = 0.0
    ) -> NDArray[np.float64]:
        """
        Calculate the moment of inertia tensor at the segment's its center of gravity.

        Args:
            ideal_density: Propellant ideal density [kg/m^3].
            web_distance: Web distance traveled [m].

        Returns:
            A 3x3 inertia tensor [kg-m^2].

        Raises:
            GrainGeometryError: If web distance exceeds web thickness or
                if no active material is found.
        """
        self._validate_web_distance(web_distance)
        z_indices, y_indices, x_indices = self._get_active_material_indices(
            web_distance
        )
        x_coords, y_coords, z_coords = self._indices_to_normalized_coords(
            z_indices, y_indices, x_indices
        )

        # Get the center of gravity
        cog = self.get_center_of_gravity(web_distance)

        # Convert to meters
        x_phys = self.map_to_length(x_coords)
        y_phys = self.map_to_length(y_coords)
        z_phys = self.map_to_length(z_coords)

        # Shift to CoG frame
        x_rel = x_phys - cog[1]
        y_rel = y_phys - cog[2]
        z_rel = z_phys - cog[0]

        # Calculate element mass
        element_volume = self.get_volume_per_element()
        element_mass = element_volume * ideal_density * self.density_ratio

        # Use core function to compute inertia tensor
        return mechanics.get_moment_of_inertia_tensor(x_rel, y_rel, z_rel, element_mass)
