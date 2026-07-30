from abc import ABC
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d

import machwave.core.filters as filters
import machwave.core.geometric as geometric
import machwave.core.mechanics as mechanics
import machwave.models.grain as grain
import machwave.models.grain.base as grain_base

from . import base as fmm_base
from . import contours as fmm_contours


class FMMGrainSegment2D(fmm_base.FMMGrainSegment, grain.GrainSegment2D, ABC):
    """Fast Marching Method (FMM) implementation for 2D grain segment."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        grid_resolution: int = fmm_base.DEFAULT_GRID_RESOLUTION,
        density_ratio: float = 1.0,
    ) -> None:
        self.face_area_interpolator: Callable[[float], float] | None = None
        self.burn_area_interpolator: Callable[[float], float] | None = None
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            grid_resolution=grid_resolution,
            density_ratio=density_ratio,
        )

    def get_coordinate_grids(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Return the coordinate grids `(map_x, map_y)`.

        Each array has shape `(grid_resolution, grid_resolution)` and ranges from -1 to 1.
        """
        if self.coordinate_grids is None:
            map_x, map_y = np.meshgrid(
                np.linspace(-1, 1, self.grid_resolution, dtype=np.float64),
                np.linspace(-1, 1, self.grid_resolution, dtype=np.float64),
            )
            self.coordinate_grids = (map_x, map_y)
        return self.coordinate_grids

    def get_outer_diameter_mask(self) -> NDArray[np.bool_]:
        """Return a boolean mask indicating which points lie outside the unit circle."""
        if self.outer_diameter_mask is None:
            map_x, map_y = self.get_coordinate_grids()
            self.outer_diameter_mask = (map_x**2 + map_y**2) > 1
        return self.outer_diameter_mask

    def _apply_surface_inhibition(
        self,
        face_map: NDArray[np.int_],
        excluded_mask: NDArray[np.bool_],
    ) -> tuple[NDArray[np.int_], NDArray[np.bool_]]:
        inner_surface_inhibited_cells = (
            (face_map == 0) if self.inhibited_surfaces.inner_surface else None
        )
        face_map, excluded_mask = super()._apply_surface_inhibition(
            face_map, excluded_mask
        )
        if inner_surface_inhibited_cells is not None:
            excluded_mask = excluded_mask | inner_surface_inhibited_cells
        return face_map, excluded_mask

    def get_contours(self, web_distance: float) -> list[NDArray[np.float64]]:
        """
        Return contour arrays for the given web distance.

        Each contour is typically an `(N, 2)` array of `(row, col)` points.
        """
        iso_level = self.normalize(web_distance)
        return fmm_contours.get_iso_contours(self.get_regression_map(), iso_level)

    def get_face_area_interpolator(self) -> Callable[[float], float]:
        """Return an interpolator mapping normalized web distance to face area [m^2]."""
        if self.face_area_interpolator is None:
            regression_map = self.get_regression_map()
            valid = np.logical_not(self.get_outer_diameter_mask())

            # Build face-area curve without per-step full-map scans
            regression_distances_sorted = np.asarray(
                regression_map[valid], dtype=np.float64
            ).ravel()
            regression_distances_sorted.sort()
            max_regression_distance = (
                float(regression_distances_sorted[-1])
                if regression_distances_sorted.size
                else 0.0
            )

            iso_level_count = int(max_regression_distance * self.grid_resolution) + 2
            iso_levels_normalized = (
                np.arange(iso_level_count, dtype=np.float64) / self.grid_resolution
            )

            count_at_or_below_level = np.searchsorted(
                regression_distances_sorted, iso_levels_normalized, side="right"
            )
            solid_cell_count = float(
                regression_distances_sorted.size
            ) - count_at_or_below_level.astype(np.float64)
            face_area_per_iso_level = np.asarray(
                self.cells_to_square_meters(solid_cell_count), dtype=np.float64
            )

            face_area_smoothed = filters.smooth_savitzky_golay(face_area_per_iso_level)
            self.face_area_interpolator = interp1d(
                iso_levels_normalized,
                face_area_smoothed,
                bounds_error=False,
                fill_value=(
                    float(face_area_smoothed[0]),
                    float(face_area_smoothed[-1]),
                ),  # type: ignore[arg-type]
                assume_sorted=True,
            )

        return self.face_area_interpolator

    def get_face_area(self, web_distance: float) -> float:
        """Return the face area at the given web distance."""
        web_distance_normalized = self.normalize(web_distance)
        return float(self.get_face_area_interpolator()(web_distance_normalized))

    def get_port_area(self, web_distance: float) -> float:
        """Return the open cross-sectional port area [m^2]."""
        face_area = self.get_face_area(web_distance)
        return geometric.get_circle_area(self.outer_diameter) - face_area

    def get_burn_area_interpolator(self) -> Callable[[float], float]:
        """Return a cached interpolator for burn area [m^2] vs normalized web."""
        if self.burn_area_interpolator is None:
            regression_map = self.get_regression_map()
            valid = np.logical_not(self.get_outer_diameter_mask())
            regression_distances_sorted = np.asarray(
                regression_map[valid], dtype=np.float64
            ).ravel()
            if regression_distances_sorted.size == 0:
                self.burn_area_interpolator = interp1d(
                    np.asarray([0.0], dtype=np.float64),
                    np.asarray([0.0], dtype=np.float64),
                    bounds_error=False,
                    fill_value=0.0,
                    assume_sorted=True,
                )
                return self.burn_area_interpolator

            regression_distances_sorted.sort()
            max_regression_distance = float(regression_distances_sorted[-1])
            iso_level_count = int(max_regression_distance * self.grid_resolution) + 2
            iso_levels_normalized = (
                np.arange(iso_level_count, dtype=np.float64) / self.grid_resolution
            )

            count_at_or_below_level = np.searchsorted(
                regression_distances_sorted, iso_levels_normalized, side="right"
            )
            solid_cell_count = float(
                regression_distances_sorted.size
            ) - count_at_or_below_level.astype(np.float64)
            face_area_per_iso_level = np.asarray(
                self.cells_to_square_meters(solid_cell_count), dtype=np.float64
            )

            core_perimeter_per_iso_level = np.empty_like(
                iso_levels_normalized, dtype=np.float64
            )
            for i, dist in enumerate(iso_levels_normalized):
                contours = fmm_contours.get_iso_contours(regression_map, float(dist))
                core_perimeter_per_iso_level[i] = float(
                    sum(
                        self.cells_to_meters(fmm_contours.get_length(contour))
                        for contour in contours
                    )
                )

            web_distances_denormalized = np.asarray(
                self.denormalize(iso_levels_normalized), dtype=np.float64
            )
            grain_length_per_web = np.asarray(
                [self.get_length(float(wd)) for wd in web_distances_denormalized],
                dtype=np.float64,
            )
            core_area_per_iso_level = (
                core_perimeter_per_iso_level * grain_length_per_web
            )
            exposed_end_count = (not self.inhibited_surfaces.upper_end) + (
                not self.inhibited_surfaces.lower_end
            )
            exposed_end_area_per_iso_level = exposed_end_count * face_area_per_iso_level
            burn_area_per_iso_level = (
                core_area_per_iso_level + exposed_end_area_per_iso_level
            )

            burn_area_smoothed = filters.smooth_savitzky_golay(burn_area_per_iso_level)
            self.burn_area_interpolator = interp1d(
                iso_levels_normalized,
                burn_area_smoothed,
                bounds_error=False,
                fill_value=(
                    float(burn_area_smoothed[0]),
                    float(burn_area_smoothed[-1]),
                ),  # type: ignore[arg-type]
                assume_sorted=True,
            )

        return self.burn_area_interpolator

    def get_burn_area(self, web_distance: float) -> float:
        """Return burn area [m^2] at a given web distance."""
        if web_distance > self.get_web_thickness():
            return 0.0
        web_distance_normalized = self.normalize(web_distance)
        value = float(self.get_burn_area_interpolator()(web_distance_normalized))
        return max(0.0, value)

    def get_core_perimeter(self, web_distance: float) -> float:
        """Return the perimeter of the open core at the given web distance."""
        contours = self.get_contours(web_distance)
        return float(
            sum(
                self.cells_to_meters(fmm_contours.get_length(contour))
                for contour in contours
            )
        )

    def get_core_area(self, web_distance: float) -> float:
        """
        Return the core (internal) area [m^2] at the given web distance.

        Computed as `perimeter * length` (2D approximation).
        """
        return self.get_core_perimeter(web_distance) * self.get_length(web_distance)

    def _validate_web_distance(self, web_distance: float) -> None:
        """
        Validate that web distance does not exceed web thickness.

        Raises:
            GrainGeometryError: If web distance exceeds web thickness.
        """
        if web_distance > self.get_web_thickness():
            raise grain.GrainGeometryError(
                "The web distance traveled is greater than the grain segment's web thickness."
            )

    def _find_solid_material_indices(
        self, web_distance: float
    ) -> tuple[NDArray[np.int_], NDArray[np.int_]]:
        """
        Get indices of active material at given web distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Tuple of (y_indices, x_indices) for active material.

        Raises:
            GrainGeometryError: If no active material is found.
        """
        y_indices, x_indices = self._get_solid_indices(web_distance)

        if len(x_indices) == 0 or len(y_indices) == 0:
            raise grain.GrainGeometryError(
                "No active material found at the given web distance."
            )

        return y_indices, x_indices

    def _indices_to_grid_coordinates(
        self, y_indices: NDArray[np.int_], x_indices: NDArray[np.int_]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Convert indices to normalized coordinates centered at origin.

        Args:
            y_indices: Y-axis indices from face map.
            x_indices: X-axis indices from face map.

        Returns:
            Tuple of (x_grid, y_grid) in normalized units.
        """
        grid_center_index = self.grid_resolution / 2
        x_grid = (x_indices - grid_center_index).astype(np.float64)
        y_grid = (y_indices - grid_center_index).astype(np.float64)
        return x_grid, y_grid

    def get_center_of_gravity(self, web_distance: float) -> NDArray[np.float64]:
        """
        Return the center of gravity of a 2D FMM grain segment.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Center of gravity as `(x, y, z)` [m], measured from the segment port.
        """
        self._validate_web_distance(web_distance)
        y_indices, x_indices = self._find_solid_material_indices(web_distance)
        x_grid, y_grid = self._indices_to_grid_coordinates(y_indices, x_indices)

        # Convert to physical coordinates
        x_denormalized = np.asarray(self.cells_to_meters(x_grid), dtype=np.float64)
        y_denormalized = np.asarray(self.cells_to_meters(y_grid), dtype=np.float64)

        # Axial bounds accounting for end face inhibition
        lower_end_recession = (
            web_distance if not self.inhibited_surfaces.lower_end else 0.0
        )
        upper_end_recession = (
            web_distance if not self.inhibited_surfaces.upper_end else 0.0
        )
        axial_center_of_gravity_position = (
            lower_end_recession + (self.length - upper_end_recession)
        ) / 2.0

        z_denormalized = np.full_like(x_denormalized, axial_center_of_gravity_position)

        return mechanics.get_center_of_gravity(
            x_denormalized, y_denormalized, z_denormalized
        )

    def get_moment_of_inertia(
        self, ideal_density: float, web_distance: float = 0.0
    ) -> NDArray[np.float64]:
        """
        Calculate the moment of inertia tensor at the segment's its center of gravity.

        Args:
            web_distance: Web distance traveled [m].
            ideal_density: Propellant ideal density [kg/m^3].

        Returns:
            A 3x3 inertia tensor [kg-m^2].
        """
        self._validate_web_distance(web_distance)
        y_indices, x_indices = self._find_solid_material_indices(web_distance)
        x_grid, y_grid = self._indices_to_grid_coordinates(y_indices, x_indices)

        current_length = self.get_length(web_distance)

        # Convert to meters
        x_denormalized = np.asarray(self.cells_to_meters(x_grid), dtype=np.float64)
        y_denormalized = np.asarray(self.cells_to_meters(y_grid), dtype=np.float64)

        # Radial CoG from the same coordinates, avoiding an index re-extraction.
        # Axial CoG is unused here: 2D elements have no axial spread.
        center_of_gravity = mechanics.get_center_of_gravity(
            x_denormalized, y_denormalized, np.zeros_like(x_denormalized)
        )

        # Coordinates relative to the center of gravity
        x_relative = x_denormalized - center_of_gravity[1]
        y_relative = y_denormalized - center_of_gravity[2]
        z_relative = np.zeros_like(x_relative)  # 2D grain, no z variation in elements

        # Total mass
        total_volume = self.get_volume(web_distance)
        total_mass = total_volume * ideal_density * self.density_ratio

        # Mass per cross-sectional element
        solid_element_count = len(x_indices)
        element_mass = total_mass / solid_element_count

        # Get base inertia from point masses (radial only)
        inertia_tensor = mechanics.get_moment_of_inertia_tensor(
            x_relative, y_relative, z_relative, element_mass
        )

        # For 2D grain (uniform along axial direction), add axial contribution
        # For a uniform rod of length L with mass M: axial_inertia_contribution = M*L^2/12 (about the center of gravity)
        axial_inertia_contribution = total_mass * current_length**2 / 12

        # Add axial contribution to radial axes (indices 1 and 2 in [z,x,y] system)
        inertia_tensor[1, 1] += axial_inertia_contribution  # Ixx (moment about x-axis)
        inertia_tensor[2, 2] += axial_inertia_contribution  # Iyy (moment about y-axis)

        return inertia_tensor
