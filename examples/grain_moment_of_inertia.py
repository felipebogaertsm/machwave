"""
Example: Calculating moment of inertia for rocket motor grains.

This example demonstrates how to calculate the moment of inertia tensor
for both single and multi-segment grain configurations. The moment of
inertia is essential for flight dynamics, stability analysis, and
trajectory modeling.
"""

import numpy as np

from machwave.models.grain import Grain
from machwave.models.grain.geometries.bates import BatesSegment
from machwave.models.grain.geometries.conical import ConicalGrainSegment
from machwave.models.grain.geometries.star import StarGrainSegment


def print_inertia_tensor(moi: np.ndarray, title: str = "Moment of Inertia Tensor"):
    """Pretty print the inertia tensor."""
    print(f"\n{title}")
    print("=" * 60)
    print("Coordinate system: [axial, radial_x, radial_y]")
    print("\nInertia Tensor [kg⋅m²]:")
    print(f"  [[{moi[0, 0]:9.6f}, {moi[0, 1]:9.6f}, {moi[0, 2]:9.6f}]")
    print(f"   [{moi[1, 0]:9.6f}, {moi[1, 1]:9.6f}, {moi[1, 2]:9.6f}]")
    print(f"   [{moi[2, 0]:9.6f}, {moi[2, 1]:9.6f}, {moi[2, 2]:9.6f}]]")
    print("\nPrincipal moments:")
    print(f"  Ixx (axial/roll):    {moi[0, 0]:.6f} kg⋅m²")
    print(f"  Iyy (radial/pitch):  {moi[1, 1]:.6f} kg⋅m²")
    print(f"  Izz (radial/yaw):    {moi[2, 2]:.6f} kg⋅m²")


def example_single_segment():
    """Example 1: Single BATES segment moment of inertia."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Single BATES Segment")
    print("=" * 60)

    segment = BatesSegment(
        outer_diameter=0.117,  # 117 mm
        core_diameter=0.045,  # 45 mm
        length=0.200,  # 200 mm
        density_ratio=1.0,
    )

    ideal_density = 1800.0  # kg/m³ (typical solid propellant)

    moi_ignition = segment.get_moment_of_inertia(
        web_distance=0.0, ideal_density=ideal_density
    )

    print_inertia_tensor(moi_ignition, "At Ignition (web_distance = 0)")

    web_thickness = segment.get_web_thickness()
    moi_half_burn = segment.get_moment_of_inertia(
        web_distance=web_thickness * 0.5, ideal_density=ideal_density
    )

    print_inertia_tensor(moi_half_burn, "At Half Burn (50% web consumed)")

    print("\nChange in MOI during burn:")
    print(f"  Ixx change: {(1 - moi_half_burn[0, 0] / moi_ignition[0, 0]) * 100:.1f}%")
    print(f"  Iyy change: {(1 - moi_half_burn[1, 1] / moi_ignition[1, 1]) * 100:.1f}%")


def example_multi_segment():
    """Example 2: Multi-segment grain assembly."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Three-Segment Grain Assembly")
    print("=" * 60)

    grain = Grain(spacing=0.010)  # 10 mm spacing

    for i in range(3):
        segment = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.150,
            density_ratio=1.0,
        )
        grain.add_segment(segment)

    ideal_density = 1800.0  # kg/m³

    grain_moi = grain.get_moment_of_inertia(
        web_distance=0.0, ideal_density=ideal_density
    )

    print_inertia_tensor(grain_moi, "Multi-Segment Grain at Ignition")

    total_mass = grain.get_propellant_mass(
        web_distance=0.0, ideal_density=ideal_density
    )
    print(f"\nTotal propellant mass: {total_mass:.4f} kg")
    print(f"Grain total length:    {grain.total_length:.3f} m")

    grain_cog = grain.get_center_of_gravity(web_distance=0.0)
    print(f"Center of gravity:     {grain_cog[0]:.4f} m from aft end")


def example_burn_progression():
    """Example 3: MOI evolution during burn."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: MOI Evolution During Burn")
    print("=" * 60)

    grain = Grain(spacing=0.005)

    for _ in range(2):
        segment = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.200,
            density_ratio=1.0,
        )
        grain.add_segment(segment)

    ideal_density = 1800.0
    web_thickness = grain.segments[0].get_web_thickness()

    burn_stages = [0.0, 0.25, 0.50, 0.75, 0.95]

    print("\nBurn Stage | Ixx [kg⋅m²] | Iyy [kg⋅m²] | Mass [kg]")
    print("-" * 60)

    for fraction in burn_stages:
        web_distance = web_thickness * fraction
        moi = grain.get_moment_of_inertia(
            web_distance=web_distance, ideal_density=ideal_density
        )
        mass = grain.get_propellant_mass(
            web_distance=web_distance, ideal_density=ideal_density
        )

        print(
            f"  {fraction * 100:5.0f}%   | {moi[0, 0]:11.8f} | {moi[1, 1]:11.8f} | {mass:8.4f}"
        )


def example_asymmetric_grain():
    """Example 4: Asymmetric grain with different density ratios."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Asymmetric Grain (Different Density Ratios)")
    print("=" * 60)

    grain = Grain(spacing=0.0)

    # First segment: full density
    segment1 = BatesSegment(
        outer_diameter=0.117,
        core_diameter=0.045,
        length=0.200,
        density_ratio=1.0,
    )

    # Second segment: 80% density (damaged or intentionally lighter)
    segment2 = BatesSegment(
        outer_diameter=0.117,
        core_diameter=0.045,
        length=0.200,
        density_ratio=0.8,
    )

    grain.add_segment(segment1)
    grain.add_segment(segment2)

    ideal_density = 1800.0
    moi = grain.get_moment_of_inertia(web_distance=0.0, ideal_density=ideal_density)

    print_inertia_tensor(moi, "Asymmetric Grain MOI")

    cog = grain.get_center_of_gravity(web_distance=0.0)
    print(
        f"\nCenter of gravity shifted to: {cog[0]:.4f} m"
        f" (vs {grain.total_length / 2:.4f} m for symmetric)"
    )


def example_2d_fmm_star_grain():
    """Example 5: 2D FMM Star Grain Segment MOI."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: 2D FMM Star Grain Segment")
    print("=" * 60)

    star_segment = StarGrainSegment(
        length=0.250,  # 250 mm
        outer_diameter=0.120,  # 120 mm
        number_of_points=5,
        point_length=0.030,  # 30 mm radial point length
        point_width=0.015,  # 15 mm point width
        density_ratio=1.0,
    )

    ideal_density = 1800.0  # kg/m³

    moi_ignition = star_segment.get_moment_of_inertia(
        web_distance=0.0, ideal_density=ideal_density
    )

    print_inertia_tensor(moi_ignition, "Star Grain at Ignition")

    web_thickness = star_segment.get_web_thickness()
    print(f"\nWeb thickness: {web_thickness * 1000:.2f} mm")

    mass = star_segment.get_mass(web_distance=0.0, ideal_density=ideal_density)
    print(f"Initial propellant mass: {mass:.4f} kg")

    moi_half_burn = star_segment.get_moment_of_inertia(
        web_distance=web_thickness * 0.5, ideal_density=ideal_density
    )

    print_inertia_tensor(moi_half_burn, "Star Grain at 50% Burn")

    print("\nMOI reduction during burn:")
    print(f"  Ixx (axial): {(1 - moi_half_burn[0, 0] / moi_ignition[0, 0]) * 100:.1f}%")
    print(
        f"  Iyy (radial): {(1 - moi_half_burn[1, 1] / moi_ignition[1, 1]) * 100:.1f}%"
    )


def example_3d_fmm_conical_grain():
    """Example 6: 3D FMM Conical Grain Segment MOI."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: 3D FMM Conical Grain Segment")
    print("=" * 60)

    conical_segment = ConicalGrainSegment(
        length=0.300,  # 300 mm
        outer_diameter=0.130,  # 130 mm
        upper_core_diameter=0.040,  # 40 mm at top
        lower_core_diameter=0.060,  # 60 mm at bottom (tapering)
        density_ratio=1.0,
    )

    ideal_density = 1800.0  # kg/m³

    moi_ignition = conical_segment.get_moment_of_inertia(
        web_distance=0.0, ideal_density=ideal_density
    )

    print_inertia_tensor(moi_ignition, "Conical Grain at Ignition")

    web_thickness = conical_segment.get_web_thickness()
    print(f"\nWeb thickness: {web_thickness * 1000:.2f} mm")

    mass = conical_segment.get_mass(web_distance=0.0, ideal_density=ideal_density)
    print(f"Initial propellant mass: {mass:.4f} kg")

    print("\nMOI Evolution During Burn:")
    print("Burn % | Ixx [kg⋅m²] | Iyy [kg⋅m²] | Izz [kg⋅m²] | Mass [kg]")
    print("-" * 70)

    for fraction in [0.0, 0.25, 0.50, 0.75, 0.95]:
        web_distance = web_thickness * fraction
        moi = conical_segment.get_moment_of_inertia(
            web_distance=web_distance, ideal_density=ideal_density
        )
        mass = conical_segment.get_mass(
            web_distance=web_distance, ideal_density=ideal_density
        )

        print(
            f" {fraction * 100:5.0f}% | {moi[0, 0]:11.8f} | {moi[1, 1]:11.8f} | "
            f"{moi[2, 2]:11.8f} | {mass:8.4f}"
        )

    print(
        "\nNote: The conical geometry creates a variable burn rate profile"
        "\nalong the grain length, with different port areas at each slice."
    )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GRAIN MOMENT OF INERTIA EXAMPLES")
    print("=" * 60)

    example_single_segment()
    example_multi_segment()
    example_burn_progression()
    example_asymmetric_grain()
    example_2d_fmm_star_grain()
    example_3d_fmm_conical_grain()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
