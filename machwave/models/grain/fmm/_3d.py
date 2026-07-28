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
    """Fast Marching Method (FMM) implementation for 3D grain segment."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        grid_resolution: int = fmm_base.DEFAULT_GRID_RESOLUTION,
        density_ratio: float = 1.0,
    ) -> None:
        self.burn_area_interpolator: Callable[[float], float] | None = None
        self.volume_interpolator: Callable[[float], float] | None = None

        # Cache center of gravity and moment of inertia shared moments per web distance
        self._mask_moments_web: float | None = None
        self._mask_moments: tuple[NDArray[np.float64], NDArray[np.float64]] | None = (
            None
        )

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            grid_resolution=grid_resolution,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        super().validate()
        self._validate_axial_resolution()

    def _validate_axial_resolution(self) -> None:
        # < 3 slices: get_port_area indexes a size-0 axis and inhibition is skipped
        axial_resolution = self.get_axial_resolution()
        if axial_resolution < 3:
            raise grain.GrainGeometryError(
                f"Axial resolution must be at least 3, got "
                f"{axial_resolution}; increase grid_resolution or the "
                f"length-to-outer-diameter ratio."
            )

    def get_axial_resolution(self) -> int:
        return round(self.grid_resolution * self.length / self.outer_diameter)

    def get_coordinate_grids(
        self,
    ) -> tuple[
        NDArray[np.float64],
        NDArray[np.float64],
        NDArray[np.float64],
    ]:
        if self.coordinate_grids is None:
            map_y, map_z, map_x = np.meshgrid(
                np.linspace(-1, 1, self.grid_resolution),
                np.linspace(1, 0, self.get_axial_resolution()),  # z axis
                np.linspace(-1, 1, self.grid_resolution),
            )

            self.coordinate_grids = (map_x, map_y, map_z)

        return self.coordinate_grids

    def get_outer_diameter_mask(self) -> NDArray[np.bool_]:
        if self.outer_diameter_mask is None:
            map_x, map_y, _ = self.get_coordinate_grids()
            self.outer_diameter_mask = (map_x**2 + map_y**2) > 1

        return self.outer_diameter_mask

    def _apply_surface_inhibition(
        self,
        face_map: NDArray[np.int_],
        excluded_mask: NDArray[np.bool_],
    ) -> tuple[NDArray[np.int_], NDArray[np.bool_]]:
        if face_map.shape[0] <= 2:
            return face_map, excluded_mask

        inner_surface_inhibited_cells = np.zeros_like(face_map, dtype=bool)
        inner_surface_inhibited_cells[1:-1] = face_map[1:-1] == 0
        inner_surface_inhibited_cells[0] = inner_surface_inhibited_cells[1]
        inner_surface_inhibited_cells[-1] = inner_surface_inhibited_cells[-2]

        # super() runs binary_erosion on the full 3D volume, which includes the
        # end-face layers in the outer_surface_boundary. Apply end inhibition AFTER so
        # those cells are not overwritten back to 0 by the outer-surface logic.
        face_map, excluded_mask = super()._apply_surface_inhibition(
            face_map, excluded_mask
        )

        if self.inhibited_surfaces.upper_end:
            end_face_inhibited_cells = (
                face_map[-1] == 0
            ) & ~inner_surface_inhibited_cells[-1]
            face_map[-1][end_face_inhibited_cells] = 1

        if self.inhibited_surfaces.lower_end:
            end_face_inhibited_cells = (
                face_map[0] == 0
            ) & ~inner_surface_inhibited_cells[0]
            face_map[0][end_face_inhibited_cells] = 1

        if self.inhibited_surfaces.inner_surface:
            excluded_mask = excluded_mask | inner_surface_inhibited_cells

        return face_map, excluded_mask

    def _compute_regression_distance(self, masked_face: np.ndarray) -> np.ndarray:
        # Regression speed needs to be calibrated for the z axes separately from the x
        # and y axes, because the 3D grid is anisotropic
        axial_grid_spacing = self.length / max(self.get_axial_resolution() - 1, 1)
        radial_grid_spacing = self.outer_diameter / (self.grid_resolution - 1)
        distance = skfmm.distance(
            masked_face,
            dx=[axial_grid_spacing, radial_grid_spacing, radial_grid_spacing],  # type: ignore[arg-type]
        )
        return distance * (2.0 / self.outer_diameter)

    def get_contours(
        self, web_distance: float, axial_position_normalized: float
    ) -> list[NDArray[np.float64]]:
        iso_level = self.normalize(web_distance)
        axial_index = int(round(axial_position_normalized))
        axial_slice = self.get_regression_map()[axial_index]
        return fmm_contours.get_iso_contours(axial_slice, iso_level)

    def get_burn_area_interpolator(self) -> Callable[[float], float]:
        """Return a cached interpolator for burn area [m^2] vs web distance [m]."""
        if self.burn_area_interpolator is None:
            regression_map = self.get_regression_map()
            regression_values = np.asarray(
                regression_map[~np.ma.getmaskarray(regression_map)], dtype=np.float64
            )
            max_iso_level = (
                float(regression_values.max()) if regression_values.size else 0.0
            )
            if max_iso_level <= 0.0:
                self.burn_area_interpolator = interp1d(
                    np.asarray([0.0], dtype=np.float64),
                    np.asarray([0.0], dtype=np.float64),
                    bounds_error=False,
                    fill_value=0.0,
                    assume_sorted=True,
                )
                return self.burn_area_interpolator

            # Lift the inhibited casing above every iso level so marching cubes
            # meshes only the burning front, not the wall.
            distance_field = np.ma.filled(regression_map, max_iso_level + 1.0)
            axial_grid_spacing = self.length / max(self.get_axial_resolution() - 1, 1)
            radial_grid_spacing = self.outer_diameter / (self.grid_resolution - 1)
            grid_spacing = (
                axial_grid_spacing,
                radial_grid_spacing,
                radial_grid_spacing,
            )

            # The iso-surface at level 0 lies on the voxelized initial face and is
            # degenerate, so sample above it and hold the first area back to web 0.
            iso_level_count = 80
            iso_levels = np.linspace(
                max_iso_level / iso_level_count, max_iso_level, iso_level_count
            )
            iso_surface_areas = np.array(
                [
                    self._compute_iso_surface_area(
                        distance_field, float(level), grid_spacing
                    )
                    for level in iso_levels
                ],
                dtype=np.float64,
            )
            web_distances_denormalized = np.concatenate(
                ([0.0], np.asarray(self.denormalize(iso_levels), dtype=np.float64))
            )
            iso_surface_areas = np.concatenate(
                ([iso_surface_areas[0]], iso_surface_areas)
            )

            burn_area_smoothed = filters.smooth_savitzky_golay(
                iso_surface_areas, window_length=9, polyorder=3
            )
            self.burn_area_interpolator = interp1d(
                web_distances_denormalized,
                burn_area_smoothed,
                bounds_error=False,
                fill_value=(
                    float(burn_area_smoothed[0]),
                    float(burn_area_smoothed[-1]),
                ),  # type: ignore[arg-type]
                assume_sorted=True,
            )

        return self.burn_area_interpolator

    @staticmethod
    def _compute_iso_surface_area(
        distance_field: NDArray[np.float64],
        level: float,
        grid_spacing: tuple[float, float, float],
    ) -> float:
        """Marching-cubes area [m^2] of one regression iso-level, 0 if empty."""
        try:
            vertices, faces, _, _ = measure.marching_cubes(
                distance_field, level=level, spacing=grid_spacing
            )
        except (ValueError, RuntimeError):
            return 0.0
        return float(measure.mesh_surface_area(vertices, faces))

    def get_burn_area(self, web_distance: float) -> float:
        if web_distance > self.get_web_thickness():
            return 0.0
        return max(0.0, float(self.get_burn_area_interpolator()(web_distance)))

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
        iso_level = self.normalize(web_distance)
        valid = np.logical_not(self.get_outer_diameter_mask())
        solid = np.logical_and(self.get_regression_map() > iso_level, valid)

        normalized_z = z / self.length
        max_index = self.get_axial_resolution() - 1
        axial_index = int(round(normalized_z * max_index))
        axial_index = (
            0
            if axial_index < 0
            else (max_index if axial_index > max_index else axial_index)
        )

        face_area = float(
            self.cells_to_square_meters(float(np.count_nonzero(solid[axial_index])))
        )
        return geometric.get_circle_area(self.outer_diameter) - face_area

    def get_minimum_port_area(self, web_distance: float) -> float:
        """
        Return the smallest port area along the segment [m^2].

        The cross section of a 3D segment varies along its length, so the flow
        passes a bottleneck: the station holding the most solid propellant.

        Args:
            web_distance: The distance traveled into the grain web.

        Returns:
            Smallest port area along the segment [m^2].
        """
        iso_level = self.normalize(web_distance)
        valid = np.logical_not(self.get_outer_diameter_mask())
        solid = np.logical_and(self.get_regression_map() > iso_level, valid)

        solid_cells_per_slice = np.count_nonzero(solid, axis=(1, 2))
        face_area = float(
            self.cells_to_square_meters(float(solid_cells_per_slice.max()))
        )
        return geometric.get_circle_area(self.outer_diameter) - face_area

    def get_voxel_volume(self) -> float:
        return (float(self.denormalize(self.get_normalized_spacing())) * 2) ** 3

    def get_volume_interpolator(self) -> Callable[[float], float]:
        """Return a cached interpolator for volume [m^3] for a web distance."""
        if self.volume_interpolator is None:
            regression_map = self.get_regression_map()
            regression_distances_sorted = np.asarray(
                regression_map[~np.ma.getmaskarray(regression_map)], dtype=np.float64
            ).ravel()
            regression_distances_sorted.sort()
            max_regression_distance = (
                float(regression_distances_sorted[-1])
                if regression_distances_sorted.size
                else 0.0
            )
            if max_regression_distance <= 0.0:
                self.volume_interpolator = interp1d(
                    np.asarray([0.0], dtype=np.float64),
                    np.asarray([0.0], dtype=np.float64),
                    bounds_error=False,
                    fill_value=0.0,
                    assume_sorted=True,
                )
                return self.volume_interpolator

            iso_level_count = int(max_regression_distance * self.grid_resolution) + 2
            iso_levels_normalized = (
                np.arange(iso_level_count, dtype=np.float64) / self.grid_resolution
            )

            count_at_or_below_level = np.searchsorted(
                regression_distances_sorted, iso_levels_normalized, side="right"
            )
            solid_voxel_count = float(
                regression_distances_sorted.size
            ) - count_at_or_below_level.astype(np.float64)
            volume_per_iso_level = solid_voxel_count * self.get_voxel_volume()

            self.volume_interpolator = interp1d(
                iso_levels_normalized,
                volume_per_iso_level,
                bounds_error=False,
                fill_value=(
                    float(volume_per_iso_level[0]),
                    float(volume_per_iso_level[-1]),
                ),  # type: ignore[arg-type]
                assume_sorted=True,
            )

        return self.volume_interpolator

    def get_volume(self, web_distance: float) -> float:
        web_distance_normalized = self.normalize(web_distance)
        return max(0.0, float(self.get_volume_interpolator()(web_distance_normalized)))

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

    def _solid_mask_moments(
        self, web_distance: float
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]] | None:
        """Centroid and second moments of the solid voxels, memoized per web."""
        if self._mask_moments_web != web_distance:
            self._mask_moments = self._compute_solid_mask_moments(web_distance)
            self._mask_moments_web = web_distance
        return self._mask_moments

    def _compute_solid_mask_moments(
        self, web_distance: float
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]] | None:
        """
        Centroid and centered second moments of the solid voxels.

        Reduces the cached boolean solid mask onto each coordinate plane and
        takes the moments as dot products with the per-axis coordinate vectors,
        so the per-voxel index arrays and conversions are never built.
        Coordinates match the index path: x and y are centered on the grid, z is
        measured from the port end.

        Returns:
            Tuple of the centroid [z, x, y] [m] and the 3x3 symmetric matrix of
            summed (r_i - cog_i)(r_j - cog_j) over the voxels, axes ordered
            [x, y, z] [m^2]. None when no solid voxels remain.
        """
        mask = self._get_solid_mask(web_distance)
        count = int(np.count_nonzero(mask))
        if count == 0:
            return None

        axial_count, y_count, x_count = mask.shape
        grid_center = self.grid_resolution / 2
        x = np.asarray(
            self.cells_to_meters(np.arange(x_count) - grid_center), dtype=np.float64
        )
        y = np.asarray(
            self.cells_to_meters(np.arange(y_count) - grid_center), dtype=np.float64
        )
        z = np.asarray(self.cells_to_meters(np.arange(axial_count)), dtype=np.float64)

        # Voxel counts projected onto each coordinate plane.
        projection_yx = mask.sum(axis=0)  # over z -> (y, x)
        projection_zx = mask.sum(axis=1)  # over y -> (z, x)
        projection_zy = mask.sum(axis=2)  # over x -> (z, y)

        count_x = projection_yx.sum(axis=0)
        count_y = projection_yx.sum(axis=1)
        count_z = projection_zx.sum(axis=1)

        # First moments: sum of each physical coordinate over the voxels.
        sum_x = count_x @ x
        sum_y = count_y @ y
        sum_z = count_z @ z
        centroid = np.array([sum_z, sum_x, sum_y], dtype=np.float64) / count

        # Second moments about the origin; the cross terms need the planar
        # projections because their two axes are coupled.
        sum_xx = count_x @ (x * x)
        sum_yy = count_y @ (y * y)
        sum_zz = count_z @ (z * z)
        sum_xy = y @ projection_yx @ x
        sum_xz = z @ projection_zx @ x
        sum_yz = z @ projection_zy @ y

        # Shift to the centroid (parallel-axis theorem on the summed moments).
        central = np.array(
            [
                [sum_xx, sum_xy, sum_xz],
                [sum_xy, sum_yy, sum_yz],
                [sum_xz, sum_yz, sum_zz],
            ],
            dtype=np.float64,
        )
        first = np.array([sum_x, sum_y, sum_z], dtype=np.float64)
        central -= np.outer(first, first) / count
        return centroid, central

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
        moments = self._solid_mask_moments(web_distance)
        if moments is None:
            raise grain.GrainGeometryError(
                "No active material found at the given web distance."
            )
        centroid, _ = moments
        # Copy so callers cannot mutate the per-web cached array.
        return centroid.copy()

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
        moments = self._solid_mask_moments(web_distance)
        if moments is None:
            raise grain.GrainGeometryError(
                "No active material found at the given web distance."
            )
        _, central_second_moments = moments

        element_mass = self.get_voxel_volume() * ideal_density * self.density_ratio
        return mechanics.get_moment_of_inertia_tensor_from_central_moments(
            central_second_moments, element_mass
        )
