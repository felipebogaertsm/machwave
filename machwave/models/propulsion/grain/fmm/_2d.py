from abc import ABC
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from machwave.core.geometric import (
    get_circle_area,
    get_contours,
    get_length,
)
from machwave.models.propulsion.grain import GrainGeometryError, GrainSegment2D

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
        inhibited_ends: int = 0,
        map_dim: int = 1000,
        density_ratio: float = 1.0,
    ) -> None:
        self.face_area_interp_func: Callable[[float], float] | None = None
        self.burn_area_interp_func: Callable[[float], float] | None = None
        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_ends=inhibited_ends,
            map_dim=map_dim,
            density_ratio=density_ratio,
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

    def get_mask(self) -> NDArray[np.bool_]:
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
        # get_contours is imported from machwave.core.math.geometric
        map_dist = self.normalize(web_distance)
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
        """
        Return the face area at the given web distance.
        """
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
            total_face_area_values = (2 - self.inhibited_ends) * face_area_values
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
        """
        Return the perimeter of the open core at the given web distance.
        """
        contours = self.get_contours(web_distance)
        # Sum the lengths of all contour segments
        return float(
            sum(
                self.map_to_length(get_length(contour, self.map_dim))
                for contour in contours
            )
        )

    def get_core_area(self, web_distance: float) -> float:
        """
        Calculate the core (internal) area at the given web distance by
        multiplying perimeter by grain segment length (a 2D approximation).
        """
        return self.get_core_perimeter(web_distance) * self.get_length(web_distance)

    def get_center_of_gravity(self, web_distance: float) -> NDArray[np.float64]:
        """
        Calculates the center of gravity of a 2D FMM grain segment at a web
        distance.

        Args:
            web_distance: Web distance traveled [m].

        Returns:
            Center of gravity [x, y, z] in meters from the port of the segment.

        Raises:
            GrainGeometryError: If web distance exceeds the web thickness, or
                if no active material is found.
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
        # Z-axis (axial): CoG is at segment center, which is length/2 from aft end
        z_cog = self.length / 2

        # NOTE: For consistency with grain coordinate system, return [z, x, y]
        return np.array([z_cog, x_cog, y_cog], dtype=np.float64)

    def get_moment_of_inertia(
        self, ideal_density: float, web_distance: float = 0.0
    ) -> NDArray[np.float64]:
        """
        Calculate the moment of inertia tensor of a 2D FMM grain segment at its center
        of gravity.

        Args:
            web_distance: Web distance traveled [m].
            ideal_density: Propellant ideal density [kg/m³].

        Returns:
            A 3x3 inertia tensor [kg-m^2] at the center of gravity:
                [[Ixx, Ixy, Ixz],
                 [Ixy, Iyy, Iyz],
                 [Ixz, Iyz, Izz]]

        Raises:
            GrainGeometryError: If web distance exceeds web thickness or
                if no active material is found.
        """
        if web_distance > self.get_web_thickness():
            raise GrainGeometryError(
                "The web distance traveled is greater than the grain "
                "segment's web thickness."
            )

        face_map = self.get_face_map(web_distance)
        mask = face_map == 1  # active material only

        y_indices, x_indices = np.where(mask)
        if len(x_indices) == 0 or len(y_indices) == 0:
            raise GrainGeometryError(
                "No active material found at the given web distance."
            )

        # Get the center of gravity to use as reference point
        cog = self.get_center_of_gravity(web_distance)
        current_length = self.get_length(web_distance)

        # Convert indices to physical coordinates
        center_shift = self.map_dim / 2
        x_coords = (x_indices - center_shift).astype(np.float64)
        y_coords = (y_indices - center_shift).astype(np.float64)

        # Convert to meters
        x_phys = self.map_to_length(x_coords)
        y_phys = self.map_to_length(y_coords)

        # Shift to CoG frame
        x_rel = x_phys - cog[1]
        y_rel = y_phys - cog[2]

        n_elements = len(x_indices)  # elements in cross section

        # Total mass
        total_volume = self.get_volume(web_distance)
        total_mass = total_volume * ideal_density * self.density_ratio

        # Mass per cross-sectional element
        dm = total_mass / n_elements

        # For axial integration: grain extends along z from 0 to current_length
        # CoG is at cog[0], so points range from -cog[0] to (current_length - cog[0])
        # For uniform density along length, we can use the formula for a rod

        # Inertia contributions:
        # Ixx (about axial axis): sum of (y² + 0²) * dm for each radial point
        # Iyy (about y-axis): sum of (x² + z²) * dm
        # Izz (about z-axis): sum of (x² + y²) * dm

        # Radial contributions (from the 2D map)
        x_sq = x_rel**2
        y_sq = y_rel**2

        # Ixx: moment about axial axis (only radial distances matter)
        Ixx = dm * np.sum(x_sq + y_sq)

        # For Iyy and Izz, we need to add the axial contribution
        # For a uniform rod from 0 to L with CoG at z_cog:
        # I_axial = M * L² / 12 (about CoG)
        I_axial = total_mass * current_length**2 / 12

        # Iyy: moment about y-axis = sum(x² + z²) dm
        Iyy = dm * np.sum(x_sq) + I_axial

        # Izz: moment about z-axis = sum(y² + z²) dm
        Izz = dm * np.sum(y_sq) + I_axial

        # Products of inertia
        Ixy = -dm * np.sum(x_rel * y_rel)
        Ixz = 0.0  # Due to symmetry along axial direction
        Iyz = 0.0  # Due to symmetry along axial direction

        # Return symmetric 3x3 tensor
        return np.array(
            [[Ixx, Ixy, Ixz], [Ixy, Iyy, Iyz], [Ixz, Iyz, Izz]], dtype=np.float64
        )
