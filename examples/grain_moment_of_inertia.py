"""
Example: Calculating moment of inertia for rocket motor grains.

This example demonstrates how to calculate the moment of inertia tensor
for both single and multi-segment grain configurations. The moment of
inertia is essential for flight dynamics, stability analysis, and
trajectory modeling.
"""

import numpy as np

from machwave.models.propulsion.grain import Grain
from machwave.models.propulsion.grain.geometries.bates import BatesSegment


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

    # Create a BATES grain segment
    segment = BatesSegment(
        outer_diameter=0.117,  # 117 mm
        core_diameter=0.045,  # 45 mm
        length=0.200,  # 200 mm
        density_ratio=1.0,
    )

    # Propellant properties
    ideal_density = 1800.0  # kg/m³ (typical solid propellant)

    # Calculate MOI at ignition
    moi_ignition = segment.get_moment_of_inertia(
        web_distance=0.0, ideal_density=ideal_density
    )

    print_inertia_tensor(moi_ignition, "At Ignition (web_distance = 0)")

    # Calculate MOI at half burn
    web_thickness = segment.get_web_thickness()
    moi_half_burn = segment.get_moment_of_inertia(
        web_distance=web_thickness * 0.5, ideal_density=ideal_density
    )

    print_inertia_tensor(moi_half_burn, "At Half Burn (50% web consumed)")

    # Show change in MOI
    print("\nChange in MOI during burn:")
    print(f"  Ixx change: {(1 - moi_half_burn[0, 0] / moi_ignition[0, 0]) * 100:.1f}%")
    print(f"  Iyy change: {(1 - moi_half_burn[1, 1] / moi_ignition[1, 1]) * 100:.1f}%")


def example_multi_segment():
    """Example 2: Multi-segment grain assembly."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Three-Segment Grain Assembly")
    print("=" * 60)

    # Create a grain with spacing between segments
    grain = Grain(spacing=0.010)  # 10 mm spacing

    # Add three identical BATES segments
    for i in range(3):
        segment = BatesSegment(
            outer_diameter=0.117,
            core_diameter=0.045,
            length=0.150,  # Shorter segments
            density_ratio=1.0,
        )
        grain.add_segment(segment)

    # Properties
    ideal_density = 1800.0  # kg/m³

    # Calculate grain MOI
    grain_moi = grain.get_moment_of_inertia(
        web_distance=0.0, ideal_density=ideal_density
    )

    print_inertia_tensor(grain_moi, "Multi-Segment Grain at Ignition")

    # Calculate total grain properties
    total_mass = grain.get_propellant_mass(
        web_distance=0.0, ideal_density=ideal_density
    )
    print(f"\nTotal propellant mass: {total_mass:.4f} kg")
    print(f"Grain total length:    {grain.total_length:.3f} m")

    # CoG location
    grain_cog = grain.get_center_of_gravity(web_distance=0.0)
    print(f"Center of gravity:     {grain_cog[0]:.4f} m from aft end")


def example_burn_progression():
    """Example 3: MOI evolution during burn."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: MOI Evolution During Burn")
    print("=" * 60)

    # Create grain
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

    # Calculate MOI at different burn stages
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

    # Show CoG shift due to density difference
    cog = grain.get_center_of_gravity(web_distance=0.0)
    print(
        f"\nCenter of gravity shifted to: {cog[0]:.4f} m"
        f" (vs {grain.total_length / 2:.4f} m for symmetric)"
    )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GRAIN MOMENT OF INERTIA EXAMPLES")
    print("=" * 60)

    example_single_segment()
    example_multi_segment()
    example_burn_progression()
    example_asymmetric_grain()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
