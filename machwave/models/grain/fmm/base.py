from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import skfmm
from scipy.ndimage import binary_erosion
from numpy.typing import NDArray

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base

MINIMUM_GRID_RESOLUTION = 100
DEFAULT_GRID_RESOLUTION = 100


class FMMGrainSegment(grain.GrainSegment, ABC):
    """Fast Marching Method (FMM) implementation of a grain segment."""

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        grid_resolution: int = DEFAULT_GRID_RESOLUTION,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize an FMM grain segment.

        Args:
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            grid_resolution: Resolution of the face map, x and y axes.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.grid_resolution = grid_resolution

        # Cache variables:
        self.coordinate_grids = None
        self.outer_diameter_mask = None
        self.masked_face = None
        self.regression_map = None
        self.web_thickness = None

        # Cache variables that only work for a specific web distance:
        self._solid_mask_web = None
        self._solid_mask = None
        self._solid_indices_web = None
        self._solid_indices = None

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
        )

    def validate(self) -> None:
        """
        Validate the internal geometry of the grain.

        Raises:
            GrainGeometryError: If the grid resolution is below the valid
                threshold.
        """
        super().validate()

        if not self.grid_resolution >= MINIMUM_GRID_RESOLUTION:
            raise grain.GrainGeometryError(
                f"Grid resolution must be at least {MINIMUM_GRID_RESOLUTION}, "
                f"got {self.grid_resolution}"
            )

    @abstractmethod
    def get_coordinate_grids(self) -> tuple:
        """Return the coordinate grids for the grain, one per spatial axis."""
        pass

    @abstractmethod
    def get_outer_diameter_mask(self) -> np.ndarray:
        """Return a boolean mask of cells outside the outer-diameter boundary."""
        pass

    @abstractmethod
    def generate_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """Generate the initial face map for the geometry (1 = propellant, 0 = void)."""
        pass

    def get_empty_face_map(self) -> np.ndarray:
        """Return a face map of all ones, shaped like the first stored map."""
        return np.ones_like(self.get_coordinate_grids()[0])

    def normalize(self, value: int | float) -> float:
        """
        Convert a dimensional value to a fraction of the outer radius.

        Args:
            value: Dimensional value (e.g., length) to normalize [m].

        Returns:
            Value expressed as a fraction of the outer radius.
        """
        return value / (0.5 * self.outer_diameter)

    def denormalize(
        self, value: int | float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """Convert a normalized input back into a dimensional value [m]."""
        return (value / 2) * (self.outer_diameter)

    def cells_to_meters(
        self, value: float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """
        Convert a pixel-distance value to [m].

        Args:
            value: Distance in pixel units.

        Returns:
            Distance [m].
        """
        return self.outer_diameter * (value / self.grid_resolution)

    def cells_to_square_meters(
        self, value: float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """
        Convert a pixel-area value to [m^2].

        Args:
            value: Area in pixel units.

        Returns:
            Area [m^2].
        """
        return (self.outer_diameter**2) * (value / (self.grid_resolution**2))

    def get_normalized_spacing(self) -> float:
        """Return the cell size in normalized coordinates (`1 / grid_resolution`)."""
        return 1 / self.grid_resolution

    def _apply_surface_inhibition(
        self,
        face_map: NDArray[np.int_],
        excluded_mask: NDArray[np.bool_],
    ) -> tuple[NDArray[np.int_], NDArray[np.bool_]]:
        """
        Apply surface inhibition maps.

        Base implementation handles outer surface inhibition. 2D and 3D subclasses add
        their own logic for other inhibited surfaces.

        Args:
            face_map: Mutable copy of the initial face map.
            excluded_mask: Mutable copy of the outer diameter mask; cells excluded from
                the burn domain, extended here with inhibited surfaces.

        Returns:
            `(face_map, excluded_mask)` with inhibition applied.
        """
        if not self.inhibited_surfaces.outer_surface:
            inside = ~excluded_mask  # Invert the mask
            eroded = binary_erosion(inside)  # Erode the inside to find the boundary
            outer_surface_boundary = inside & np.logical_not(eroded)
            face_map[outer_surface_boundary] = 0

        return face_map, excluded_mask

    def get_masked_face(self) -> np.ndarray:
        """Return a masked representation of the face map."""
        if self.masked_face is None:
            face_map = self.generate_initial_face_map().copy()
            excluded_mask = self.get_outer_diameter_mask().copy()

            face_map, excluded_mask = self._apply_surface_inhibition(
                face_map, excluded_mask
            )

            self.masked_face = np.ma.MaskedArray(face_map, excluded_mask)
        return self.masked_face

    @property
    def has_cross_section_regression(self) -> bool:
        """Return whether the cross-section has any burning surface."""
        masked_face = self.get_masked_face()
        unmasked = ~np.ma.getmaskarray(masked_face)
        return bool(np.any(masked_face.data[np.asarray(unmasked, dtype=bool)] == 0))

    def _compute_regression_distance(self, masked_face: np.ndarray) -> np.ndarray:
        """Return the regression distance from the burning surface in normalized web units."""
        return skfmm.distance(masked_face, dx=self.get_normalized_spacing()) * 2

    def get_regression_map(self):
        """
        Return the distance map for grain regression.

        Uses the fast marching method (scikit-fmm) on the masked face. Each
        value is the distance from the initial face along the cross-section.
        With no burning surface (end burner), returns a static map set to the
        axial burnout web, so the grain regresses along its length, not a cell.
        """
        if self.regression_map is None:
            masked_face = self.get_masked_face()

            if self.has_cross_section_regression:
                self.regression_map = self._compute_regression_distance(masked_face)
            else:
                # End burner: web = length split across exposed ends. Fill the
                # whole array with one constant (not 0 outside the mask) so the
                # perimeter tracer finds no spurious contour.
                exposed_end_count = (not self.inhibited_surfaces.upper_end) + (
                    not self.inhibited_surfaces.lower_end
                )
                normalized_axial_web_distance = (
                    self.normalize(self.length / exposed_end_count)
                    if exposed_end_count
                    else 0.0
                )
                self.regression_map = np.ma.MaskedArray(
                    np.full(masked_face.shape, normalized_axial_web_distance),
                    mask=np.ma.getmaskarray(masked_face),
                )
        return self.regression_map

    def get_web_thickness(self) -> float:
        """
        Return the maximum web thickness of the grain [m].

        Derived from the distance map as the largest normalized distance,
        converted back into real units.
        """
        if self.web_thickness is None:
            self.web_thickness = float(
                self.denormalize(float(np.amax(self.get_regression_map())))
            )
        return float(self.web_thickness)

    def get_face_map(self, web_distance: float) -> np.typing.NDArray[np.int64]:
        """
        Returns a matrix representing the grain face based on the given web distance.

        The returned array can contain:
        -1 for masked or invalid points,
        0 for points below the threshold,
        1 for points above the threshold.

        Args:
            web_distance: The distance traveled into the grain web.

        Returns:
            A NumPy array with -1, 0, or 1 indicating the grain face at the specified web distance.
        """
        web_distance_normalized = self.normalize(web_distance)
        regression_map = self.get_regression_map()
        excluded_mask = np.ma.getmaskarray(regression_map)

        # Create a masked array, where excluded cells are masked out
        occupancy_state = np.ma.MaskedArray(
            (regression_map > web_distance_normalized).astype(np.int64),
            mask=excluded_mask,
        )

        # Fill masked entries with -1, valid/true entries remain 1 or 0
        return occupancy_state.filled(-1)

    def _get_solid_mask(self, web_distance: float) -> NDArray[np.bool_]:
        """
        Boolean mask of solid (unburned, in-domain) cells at a web distance.

        Equivalent to `get_face_map(web_distance) == 1` but built as a plain
        boolean array, skipping the int64/MaskedArray/`filled(-1)` path. The
        per-step consumers (volume, indices) route through this instead of
        `get_face_map`, whose -1/0/1 encoding is kept for plot consumers.
        """
        if self._solid_mask is None or self._solid_mask_web != web_distance:
            regression_map = self.get_regression_map()
            web_distance_normalized = self.normalize(web_distance)
            excluded_mask = np.ma.getmaskarray(regression_map)
            self._solid_mask = (
                np.ma.getdata(regression_map) > web_distance_normalized
            ) & ~excluded_mask
            self._solid_mask_web = web_distance
        return self._solid_mask

    def _get_solid_indices(self, web_distance: float) -> tuple[NDArray[np.int_], ...]:
        """Indices of solid cells (`np.where` over the cached mask), memoized."""
        if self._solid_indices is None or self._solid_indices_web != web_distance:
            self._solid_indices = np.where(self._get_solid_mask(web_distance))
            self._solid_indices_web = web_distance
        return self._solid_indices

    @abstractmethod
    def get_contours(
        self, web_distance: float, *args: Any, **kwargs: Any
    ) -> list[NDArray[np.float64]]:
        """
        Return the contours of the regression map for a given web distance.

        Must be implemented by a subclass to compute the contour data based on
        the given web distance and any additional parameters.

        Args:
            web_distance: Depth of regression into the grain web [m].
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            An array representing the computed contours of the grain regression.
        """
        pass
