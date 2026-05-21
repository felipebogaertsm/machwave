from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import skfmm
from scipy.ndimage import binary_erosion
from numpy.typing import NDArray

import machwave.models.grain as grain
import machwave.models.grain.base as grain_base

MINIMUM_MAP_DIMENSION = 100


class FMMGrainSegment(grain.GrainSegment, ABC):
    """
    Fast Marching Method (FMM) implementation of a grain segment.

    This class was inspired by the Andrew Reilley's software openMotor, in
    particular the fmm module.
    openMotor's repository can be accessed at:
    https://github.com/reilleya/openMotor
    """

    def __init__(
        self,
        map_dim: int,
        length: float,
        outer_diameter: float,
        inhibited_surfaces: grain_base.InhibitedSurfaces | None = None,
        density_ratio: float = 1.0,
    ) -> None:
        """
        Initialize an FMM grain segment.

        Args:
            map_dim: Pixel resolution of the cross-section map.
            length: Segment length [m].
            outer_diameter: Outer diameter [m].
            inhibited_surfaces: Surfaces inhibited from burning.
            density_ratio: Ratio of real to ideal propellant density.
        """
        self.map_dim = map_dim

        # "Cache" variables:
        self.maps = None
        self.mask = None
        self.masked_face = None
        self.regression_map = None
        self.web_thickness = None

        super().__init__(
            length=length,
            outer_diameter=outer_diameter,
            inhibited_surfaces=inhibited_surfaces,
            density_ratio=density_ratio,
        )

    @abstractmethod
    def get_initial_face_map(self) -> np.typing.NDArray[np.int_]:
        """Method needs to be implemented for each and every geometry."""
        pass

    @abstractmethod
    def get_maps(self) -> tuple:
        """
        Return the coordinate maps for the grain.

        Returns:
            `(map_x, map_y)` for 2D; `(map_x, map_y, map_z)` for 3D.
        """
        pass

    @abstractmethod
    def get_mask(self) -> np.ndarray:
        """Implementation varies depending if the geometry is 2D or 3D."""
        pass

    def validate(self) -> None:
        """
        Validate the internal geometry of the grain.

        Ensures the grain map dimension meets the minimum required size.

        Raises:
            GrainGeometryError: If the grain map dimension is below the valid
                threshold.
        """
        super().validate()
        if not self.map_dim >= MINIMUM_MAP_DIMENSION:
            raise grain.GrainGeometryError(
                f"Map dimension must be at least {MINIMUM_MAP_DIMENSION}, "
                f"got {self.map_dim}"
            )

    def normalize(self, value: int | float) -> float:
        """
        Convert a dimensional value to a fraction of the half-diameter.

        Args:
            value: Dimensional value (e.g., length) to normalize [m].

        Returns:
            Value expressed as a fraction of the half-diameter.
        """
        return value / (0.5 * self.outer_diameter)

    def denormalize(
        self, value: int | float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """Convert a normalized input back into a dimensional value [m]."""
        return (value / 2) * (self.outer_diameter)

    def map_to_area(
        self, value: float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """
        Convert a pixel-area value to [m^2].

        Scales by `outer_diameter^2 / map_dim^2`.

        Args:
            value: Area in pixel units.

        Returns:
            Area [m^2].
        """
        return (self.outer_diameter**2) * (value / (self.map_dim**2))

    def map_to_length(
        self, value: float | NDArray[np.float64]
    ) -> float | NDArray[np.float64]:
        """
        Convert a pixel-distance value to [m].

        Scales by `outer_diameter / map_dim`.

        Args:
            value: Distance in pixel units.

        Returns:
            Distance [m].
        """
        return self.outer_diameter * (value / self.map_dim)

    def get_empty_face_map(self) -> np.ndarray:
        """Return a face map of all ones, shaped like the first stored map."""
        return np.ones_like(self.get_maps()[0])

    def _apply_inhibition(
        self,
        face_map: NDArray[np.int_],
        outside: NDArray[np.bool_],
    ) -> tuple[NDArray[np.int_], NDArray[np.bool_]]:
        """
        Apply surface-inhibition adjustments to the face map and mask.

        Base implementation handles outer-surface inhibition. 2D and 3D
        subclasses add their own logic for other inhibited surfaces.

        Args:
            face_map: Mutable copy of the initial face map.
            outside: Mutable copy of the circular boundary mask.

        Returns:
            Tuple `(face_map, outside)` with inhibition applied.
        """
        if not self.inhibited_surfaces.outer_surface:
            inside = ~outside  # Invert the mask
            eroded = binary_erosion(inside)  # Erode the inside to find the boundary
            boundary_ring = inside & np.logical_not(eroded)
            face_map[boundary_ring] = 0

        return face_map, outside

    def get_masked_face(self) -> np.ndarray:
        """
        Return a masked representation of the face map.

        The mask is circular and normalized to the map dimensions. Generated on
        first access by combining the initial face map with the circular mask.
        """
        if self.masked_face is None:
            face_map = self.get_initial_face_map().copy()
            outside = self.get_mask().copy()

            face_map, outside = self._apply_inhibition(face_map, outside)

            self.masked_face = np.ma.MaskedArray(face_map, outside)
        return self.masked_face

    def get_cell_size(self) -> float:
        """Return the cell size in normalized coordinates (`1 / map_dim`)."""
        return 1 / self.map_dim

    @property
    def has_cross_section_regression(self) -> bool:
        """
        Return whether the cross-section has any burning surface.

        Inspects the masked face map for zero-valued (burning) cells. Returns
        False when no burning front exists for the FMM to propagate from.
        """
        masked_face = self.get_masked_face()
        unmasked = ~np.ma.getmaskarray(masked_face)
        return bool(np.any(masked_face.data[np.asarray(unmasked, dtype=bool)] == 0))

    def get_regression_map(self):
        """
        Return the distance map for grain regression.

        Uses the fast marching method (scikit-fmm) on the masked face. Each
        value represents the distance from the initial face along the
        cross-section of the grain. When the cross-section has no burning
        surface (end burner), a static map is returned instead.
        """
        if self.regression_map is None:
            masked_face = self.get_masked_face()

            if self.has_cross_section_regression:
                self.regression_map = (
                    skfmm.distance(masked_face, dx=self.get_cell_size()) * 2
                )
            else:
                unmasked = ~np.ma.getmaskarray(masked_face)
                self.regression_map = np.ma.MaskedArray(
                    np.where(unmasked, self.get_cell_size(), 0.0),
                    mask=~unmasked,
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
        invalid = np.ma.getmaskarray(regression_map)

        # Create a masked array, where invalid cells are masked out
        maskarr = np.ma.MaskedArray(
            (regression_map > web_distance_normalized).astype(np.int64),
            mask=invalid,
        )

        # Fill masked entries with -1, valid/true entries remain 1 or 0
        return maskarr.filled(-1)
