"""Mechanics calculations."""

import numpy as np
import numpy.typing as npt


def get_center_of_gravity(
    x_coords: npt.NDArray[np.float64],
    y_coords: npt.NDArray[np.float64],
    z_coords: npt.NDArray[np.float64],
    masses: npt.NDArray[np.float64] | None = None,
) -> npt.NDArray[np.float64]:
    """
    Calculate center of gravity from point mass elements.

    Computes the center of gravity (centroid) of a collection of point masses.
    The coordinate system is [z, x, y] where z is the axial direction.

    Args:
        x_coords: X-coordinates of elements [m].
        y_coords: Y-coordinates of elements [m].
        z_coords: Z-coordinates (axial) of elements [m].
        masses: Mass of each element [kg]. If None, assumes equal mass for all elements.

    Returns:
        Center of gravity as [z, x, y] in meters.

    Raises:
        ValueError: If coordinate arrays have different lengths, if masses array
            length doesn't match coordinates or if total mass is zero.
    """
    if not (len(x_coords) == len(y_coords) == len(z_coords)):
        raise ValueError("All coordinate arrays must have the same length")

    if masses is not None:
        if len(masses) != len(x_coords):
            raise ValueError("Mass array length must match coordinate arrays")
        total_mass = np.sum(masses)
        if total_mass == 0:
            raise ValueError("Total mass cannot be zero")
        x_cog = np.sum(x_coords * masses) / total_mass
        y_cog = np.sum(y_coords * masses) / total_mass
        z_cog = np.sum(z_coords * masses) / total_mass
    else:
        x_cog = np.mean(x_coords)
        y_cog = np.mean(y_coords)
        z_cog = np.mean(z_coords)

    return np.array([z_cog, x_cog, y_cog], dtype=np.float64)


def get_moment_of_inertia_tensor(
    x_coords: npt.NDArray[np.float64],
    y_coords: npt.NDArray[np.float64],
    z_coords: npt.NDArray[np.float64],
    element_mass: float,
) -> npt.NDArray[np.float64]:
    """
    Calculate moment of inertia tensor from point mass elements.

    Computes the 3x3 inertia tensor for a collection of point masses at given
    coordinates. All coordinates should be relative to the center of gravity. The
    coordinate system is [z, x, y] where z is the axial direction. Assumes constant
    density for all elements.

    Args:
        x_coords: X-coordinates of elements relative to CoG [m].
        y_coords: Y-coordinates of elements relative to CoG [m].
        z_coords: Z-coordinates (axial) of elements relative to CoG [m].
        element_mass: Mass per element [kg].

    Returns:
        3x3 symmetric inertia tensor [kg-m^2] in coordinate system [z, x, y].

    Raises:
        ValueError: If coordinate arrays have different lengths.
    """
    if not (len(x_coords) == len(y_coords) == len(z_coords)):
        raise ValueError("All coordinate arrays must have the same length")

    x_sq = x_coords**2
    y_sq = y_coords**2
    z_sq = z_coords**2

    Ixx = element_mass * np.sum(y_sq + z_sq)
    Iyy = element_mass * np.sum(x_sq + z_sq)
    Izz = element_mass * np.sum(x_sq + y_sq)

    Ixy = -element_mass * np.sum(x_coords * y_coords)
    Ixz = -element_mass * np.sum(x_coords * z_coords)
    Iyz = -element_mass * np.sum(y_coords * z_coords)

    return np.array(
        [[Izz, Ixz, Iyz], [Ixz, Ixx, Ixy], [Iyz, Ixy, Iyy]], dtype=np.float64
    )
