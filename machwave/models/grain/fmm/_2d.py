from abc import ABC
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from machwave.core.geometric import get_circle_area
from machwave.core.mechanics import (
    get_center_of_gravity,
    get_moment_of_inertia_tensor,
)
from machwave.models.grain import GrainGeometryError, GrainSegment2D
from machwave.models.grain.base import InhibitedSurfaces

from .base import FMMGrainSegment
from .contours import get_contours, get_length


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
        inhibited_surfaces: InhibitedSurfaces | None = None,
        map_dim: int = 100,
        density_ratio: float = 1.0,
    ) -> None:
        self.face_area_interp_func: Callable[[float], float] | None = None
        self.burn_area_interp_func: Callable[[float], float] | None = None
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            map_dim=map_dim,
            density_ratio=density_ratio,
        )

    def get_maps(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Return the coordinate maps `(map_x, map_y)`.

        Each array has shape `(map_dim, map_dim)` and ranges from -1 to 1.
        """
        if self.maps is None:
            map_x, map_y = np.meshgrid(
                np.linspace(-1, 1, self.map_dim, dtype=np.float64),
                np.linspace(-1, 1, self.map_dim, dtype=np.float64),
            )
            self.maps = (map_x, map_y)
        return self.maps

    def get_mask(self) -> NDArray[np.bool_]:
        """Return a boolean mask indicating which points lie outside the unit circle."""
        if self.mask is None:
            map_x, map_y = self.get_maps()
            self.mask = (map_x**2 + map_y**2) > 1
        return self.mask

    def _apply_inhibition(
        self,
        face_map: NDArray[np.int_],
        outside: NDArray[np.bool_],
    ) -> tuple[NDArray[np.int_], NDArray[np.bool_]]:
        bore_mask = (face_map == 0) if self.inhibited_surfaces.inner_surface else None
        face_map, outside = super()._apply_inhibition(face_map, outside)
        if bore_mask is not None:
            outside = outside | bore_mask
        return face_map, outside

    def get_contours(self, web_distance: float) -> list[NDArray[np.float64]]:
        """
        Return contour arrays for the given web distance.

        Each contour is typically an `(N, 2)` array of `(row, col)` points.
        """
        map_dist = self.normalize(web_distance)
        return get_contours(self.get_regression_map(), map_dist)

    def get_port_area(self, web_distance: float) -> float:
        """Return the open cross-sectional port area [m^2]."""
        face_area = self.get_face_area(web_distance)
        return get_circle_area(self.outer_diameter) - face_area

    def get_face_area_interp_func(self) -> Callable[[float], float]:
        """Return an interpolator mapping normalized web distance to face area [m^2]."""
        if self.face_area_interp_func is None:
            regression_map = self.get_regression_map()
            valid = np.logical_not(self.get_mask())

            # Build face-area curve without per-step full-map scans
            values = np.asarray(regression_map[valid], dtype=np.float64).ravel()
            values.sort()
            max_dist = float(values[-1]) if values.size else 0.0

            step_count = int(max_dist * self.map_dim) + 2
            distances = np.arange(step_count, dtype=np.float64) / self.map_dim

            n_le = np.searchsorted(values, distances, side="right")
            counts = float(values.size) - n_le.astype(np.float64)
            face_area_values = np.asarray(self.map_to_area(counts), dtype=np.float64)

            # Smooth + interpolate (adapt for small arrays)
            smoothed = face_area_values
            if face_area_values.size >= 7:
                window_length = min(31, int(face_area_values.size))
                if window_length % 2 == 0:
                    window_length -= 1
                polyorder = min(5, window_length - 2)
                if window_length >= 3 and polyorder >= 1:
                    smoothed = savgol_filter(face_area_values, window_length, polyorder)

            smoothed_arr = np.asarray(smoothed, dtype=np.float64)
            self.face_area_interp_func = interp1d(
                distances,
                smoothed_arr,
                bounds_error=False,
                fill_value=(float(smoothed_arr[0]), float(smoothed_arr[-1])),  # type: ignore[arg-type]
                assume_sorted=True,
            )

        return self.face_area_interp_func

    def get_face_area(self, web_distance: float) -> float:
        """Return the face area at the given web distance."""
        map_distance = self.normalize(web_distance)
        return float(self.get_face_area_interp_func()(map_distance))

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
                    fill_value=0.0,
                    assume_sorted=True,
                )
                return self.burn_area_interp_func

            values.sort()
            max_dist = float(values[-1])
            step_count = int(max_dist * self.map_dim) + 2
            distances = np.arange(step_count, dtype=np.float64) / self.map_dim

            n_le = np.searchsorted(values, distances, side="right")
            counts = float(values.size) - n_le.astype(np.float64)
            face_area_values = np.asarray(self.map_to_area(counts), dtype=np.float64)

            perimeter_values = np.empty_like(distances, dtype=np.float64)
            for i, dist in enumerate(distances):
                contours = get_contours(regression_map, float(dist))
                perimeter_values[i] = float(
                    sum(
                        self.map_to_length(get_length(contour, self.map_dim))
                        for contour in contours
                    )
                )

            web_distances = np.asarray(self.denormalize(distances), dtype=np.float64)
            length_values = np.asarray(
                [self.get_length(float(wd)) for wd in web_distances], dtype=np.float64
            )
            core_area_values = perimeter_values * length_values
            exposed_ends = (not self.inhibited_surfaces.upper_end) + (
                not self.inhibited_surfaces.lower_end
            )
            total_face_area_values = exposed_ends * face_area_values
            burn_area_values = core_area_values + total_face_area_values

            smoothed = burn_area_values
            if burn_area_values.size >= 7:
                window_length = min(31, int(burn_area_values.size))
                if window_length % 2 == 0:
                    window_length -= 1
                polyorder = min(5, window_length - 2)
                if window_length >= 3 and polyorder >= 1:
                    smoothed = savgol_filter(burn_area_values, window_length, polyorder)

            smoothed_arr = np.asarray(smoothed, dtype=np.float64)
            self.burn_area_interp_func = interp1d(
                distances,
                smoothed_arr,
                bounds_error=False,
                fill_value=(float(smoothed_arr[0]), float(smoothed_arr[-1])),  # type: ignore[arg-type]
                assume_sorted=True,
            )

        return self.burn_area_interp_func

    def get_burn_area(self, web_distance: float) -> float:
        """Return burn area [m^2] at a given web distance."""
        if web_distance > self.get_web_thickness():
            return 0.0
        map_distance = self.normalize(web_distance)
        value = float(self.get_burn_area_interp_func()(map_distance))
        return max(0.0, value)

    def get_core_perimeter(self, web_distance: float) -> float:
        """Return the perimeter of the open core at the given web distance."""
        contours = self.get_contours(web_distance)
        return float(
            sum(
                self.map_to_length(get_length(contour, self.map_dim))
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
            raise GrainGeometryError(
                "The web distance traveled is greater than the grain segment's web thickness."
            )

    def _get_active_material_indices(
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
        face_map = self.get_face_map(web_distance)
        mask = face_map == 1  # active material only
        y_indices, x_indices = np.where(mask)

        if len(x_indices) == 0 or len(y_indices) == 0:
            raise GrainGeometryError(
                "No active material found at the given web distance."
            )

        return y_indices, x_indices

    def _indices_to_normalized_coords(
        self, y_indices: NDArray[np.int_], x_indices: NDArray[np.int_]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Convert indices to normalized coordinates centered at origin.

        Args:
            y_indices: Y-axis indices from face map.
            x_indices: X-axis indices from face map.

        Returns:
            Tuple of (x_coords, y_coords) in normalized units.
        """
        center_shift = self.map_dim / 2
        x_coords = (x_indices - center_shift).astype(np.float64)
        y_coords = (y_indices - center_shift).astype(np.float64)
        return x_coords, y_coords

    def get_center_of_gravity(self, web_distance: float) -> NDArray[np.float64]:
        """
        Return the center of gravity of a 2D FMM grain segment.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Center of gravity [x, y, z] [m], measured from the segment port.
        """
        self._validate_web_distance(web_distance)
        y_indices, x_indices = self._get_active_material_indices(web_distance)
        x_coords, y_coords = self._indices_to_normalized_coords(y_indices, x_indices)

        # Convert to physical coordinates
        x_phys = np.asarray(self.map_to_length(x_coords), dtype=np.float64)
        y_phys = np.asarray(self.map_to_length(y_coords), dtype=np.float64)

        # Axial bounds accounting for end face inhibition
        lower_recession = web_distance if not self.inhibited_surfaces.lower_end else 0.0
        upper_recession = web_distance if not self.inhibited_surfaces.upper_end else 0.0
        axial_cog = (lower_recession + (self.length - upper_recession)) / 2.0

        z_phys = np.full_like(x_phys, axial_cog)

        return get_center_of_gravity(x_phys, y_phys, z_phys)

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
        y_indices, x_indices = self._get_active_material_indices(web_distance)
        x_coords, y_coords = self._indices_to_normalized_coords(y_indices, x_indices)

        # Get the center of gravity to use as reference point
        cog = self.get_center_of_gravity(web_distance)
        current_length = self.get_length(web_distance)

        # Convert to meters
        x_phys = self.map_to_length(x_coords)
        y_phys = self.map_to_length(y_coords)

        # Shift to CoG frame
        x_rel = x_phys - cog[1]
        y_rel = y_phys - cog[2]
        z_rel = np.zeros_like(x_rel)  # 2D grain, no z variation in elements

        # Total mass
        total_volume = self.get_volume(web_distance)
        total_mass = total_volume * ideal_density * self.density_ratio

        # Mass per cross-sectional element
        n_elements = len(x_indices)
        element_mass = total_mass / n_elements

        # Get base inertia from point masses (radial only)
        moi = get_moment_of_inertia_tensor(x_rel, y_rel, z_rel, element_mass)

        # For 2D grain (uniform along axial direction), add axial contribution
        # For a uniform rod of length L with mass M: I_axial = M*L^2/12 (about CoG)
        I_axial = total_mass * current_length**2 / 12

        # Add axial contribution to radial axes (indices 1 and 2 in [z,x,y] system)
        moi[1, 1] += I_axial  # Ixx (moment about x-axis)
        moi[2, 2] += I_axial  # Iyy (moment about y-axis)

        return moi
