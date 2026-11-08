"""Mechanics calculations."""

from collections.abc import Sequence

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


def get_moment_of_inertia_tensor_from_central_moments(
    central_second_moments: npt.NDArray[np.float64],
    element_mass: float,
) -> npt.NDArray[np.float64]:
    """
    Build the inertia tensor from centroid-relative second moments.

    Equivalent to get_moment_of_inertia_tensor but takes the already summed second
    moments of the elements instead of per-element coordinates, so the caller can supply
    them without materializing one coordinate per element.

    Args:
        central_second_moments: 3x3 symmetric matrix whose entry (i, j) is the sum over
            elements of (r_i - cog_i)(r_j - cog_j), axes ordered [x, y, z] [m^2].
        element_mass: Mass per element [kg].

    Returns:
        3x3 symmetric inertia tensor [kg-m^2] in coordinate system [z, x, y].
    """
    s_xx = central_second_moments[0, 0]
    s_yy = central_second_moments[1, 1]
    s_zz = central_second_moments[2, 2]
    s_xy = central_second_moments[0, 1]
    s_xz = central_second_moments[0, 2]
    s_yz = central_second_moments[1, 2]

    Ixx = element_mass * (s_yy + s_zz)
    Iyy = element_mass * (s_xx + s_zz)
    Izz = element_mass * (s_xx + s_yy)

    Ixy = -element_mass * s_xy
    Ixz = -element_mass * s_xz
    Iyz = -element_mass * s_yz

    return np.array(
        [[Izz, Ixz, Iyz], [Ixz, Ixx, Ixy], [Iyz, Ixy, Iyy]], dtype=np.float64
    )


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

    s_xx = np.sum(x_coords * x_coords)
    s_yy = np.sum(y_coords * y_coords)
    s_zz = np.sum(z_coords * z_coords)
    s_xy = np.sum(x_coords * y_coords)
    s_xz = np.sum(x_coords * z_coords)
    s_yz = np.sum(y_coords * z_coords)

    central_second_moments = np.array(
        [[s_xx, s_xy, s_xz], [s_xy, s_yy, s_yz], [s_xz, s_yz, s_zz]], dtype=np.float64
    )
    return get_moment_of_inertia_tensor_from_central_moments(
        central_second_moments, element_mass
    )


def get_solid_cylinder_moment_of_inertia(
    mass: float, length: float, radius: float
) -> npt.NDArray[np.float64]:
    """
    Calculate the inertia tensor of a uniform solid cylinder lying along the x-axis.

    I_xx = m r^2 / 2 about the cylinder axis and I_yy = I_zz = m (r^2 / 4 + L^2 / 12)
    about any transverse axis, both through the center of gravity.

    References:
        Meriam, J. L., & Kraige, L. G. (2012). *Engineering Mechanics: Dynamics*
        (7th ed.). Wiley. Appendix D, Table D/4 (circular cylinder).

    Args:
        mass: Cylinder mass [kg].
        length: Cylinder length along its axis [m].
        radius: Cylinder radius [m].

    Returns:
        3x3 diagonal inertia tensor at the center of gravity, axial axis first
        [kg-m^2].
    """
    axial_moment = mass * radius**2 / 2
    transverse_moment = mass * (radius**2 / 4 + length**2 / 12)
    return np.diag([axial_moment, transverse_moment, transverse_moment]).astype(
        np.float64
    )


def get_combined_mass_properties(
    masses: Sequence[float],
    centers_of_gravity: Sequence[npt.NDArray[np.float64]],
    moments_of_inertia: Sequence[npt.NDArray[np.float64]],
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Combine rigid bodies into one with the parallel axis theorem.

    Each body's inertia tensor is shifted from its own center of gravity to the
    combined one by m (|r|^2 E - r r^T), where r joins the two. A massless body adds
    nothing, so its center of gravity may be undefined.

    References:
        Meriam, J. L., & Kraige, L. G. (2012). *Engineering Mechanics: Dynamics*
        (7th ed.). Wiley. Appendix B (parallel-axis theorem).

    Args:
        masses: Mass of each body [kg].
        centers_of_gravity: Center of gravity of each body, in one shared frame [m].
        moments_of_inertia: 3x3 inertia tensor of each body about its own center of
            gravity, axes parallel to the shared frame [kg-m^2].

    Returns:
        The combined center of gravity [m] and the inertia tensor about it
        [kg-m^2]. With no mass, the center of gravity is NaN and the inertia zero,
        as the solid simulation records an empty grain.
    """
    total_mass = 0.0
    weighted_position = np.zeros(3, dtype=np.float64)
    for mass, center_of_gravity in zip(masses, centers_of_gravity, strict=True):
        if mass > 0.0:
            total_mass += mass
            weighted_position += mass * np.asarray(center_of_gravity)

    if total_mass <= 0.0:
        return np.full(3, np.nan), np.zeros((3, 3), dtype=np.float64)

    combined_center_of_gravity = weighted_position / total_mass
    combined_moment_of_inertia = np.zeros((3, 3), dtype=np.float64)
    for mass, center_of_gravity, moment_of_inertia in zip(
        masses, centers_of_gravity, moments_of_inertia, strict=True
    ):
        if mass > 0.0:
            offset = np.asarray(center_of_gravity) - combined_center_of_gravity
            combined_moment_of_inertia += moment_of_inertia + mass * (
                np.dot(offset, offset) * np.eye(3) - np.outer(offset, offset)
            )
    return combined_center_of_gravity, combined_moment_of_inertia
