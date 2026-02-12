"""
Pytest configuration for FMM grain MOI tests.

Reuses fixtures from CoG tests for parametrization.
"""

import pytest

from machwave.models.propulsion.grain.geometries.conical import ConicalGrainSegment
from machwave.models.propulsion.grain.geometries.d_grain import DGrainSegment
from machwave.models.propulsion.grain.geometries.multi_port import (
    MultiPortGrainSegment,
)
from machwave.models.propulsion.grain.geometries.rod_and_tube import (
    RodAndTubeGrainSegment,
)
from machwave.models.propulsion.grain.geometries.star import StarGrainSegment
from machwave.models.propulsion.grain.geometries.wagon_wheel import (
    WagonWheelGrainSegment,
)


def create_star_segment(
    length=1.0,
    outer_diameter=0.1,
    density_ratio=1.0,
):
    """Factory for creating StarGrainSegment instances."""
    return StarGrainSegment(
        length=length,
        outer_diameter=outer_diameter,
        number_of_points=5,
        point_length=0.035,
        point_width=0.01,
        density_ratio=density_ratio,
    )


def create_wagon_wheel_segment(
    length=1.0,
    outer_diameter=0.1,
    density_ratio=1.0,
):
    """Factory for creating WagonWheelGrainSegment instances."""
    return WagonWheelGrainSegment(
        length=length,
        outer_diameter=outer_diameter,
        core_diameter=0.02,
        number_of_ports=6,
        port_inner_diameter=0.03,
        port_outer_diameter=0.045,
        port_angular_width=0.1,
        density_ratio=density_ratio,
    )


def create_rod_and_tube_segment(
    length=1.0,
    outer_diameter=0.1,
    density_ratio=1.0,
):
    """Factory for creating RodAndTubeGrainSegment instances."""
    return RodAndTubeGrainSegment(
        length=length,
        outer_diameter=outer_diameter,
        rod_outer_diameter=0.01,
        tube_inner_diameter=0.03,
        density_ratio=density_ratio,
    )


def create_multi_port_segment(
    length=1.0,
    outer_diameter=0.1,
    density_ratio=1.0,
):
    """Factory for creating MultiPortGrainSegment instances."""
    return MultiPortGrainSegment(
        length=length,
        outer_diameter=outer_diameter,
        port_diameter=0.015,
        port_radial_count=3,
        port_level_count=1,
        density_ratio=density_ratio,
    )


def create_d_grain_segment(
    length=1.0,
    outer_diameter=0.1,
    density_ratio=1.0,
):
    """Factory for creating DGrainSegment instances."""
    return DGrainSegment(
        length=length,
        outer_diameter=outer_diameter,
        slot_offset=0.02,
        density_ratio=density_ratio,
    )


def create_conical_segment(
    length=1.0,
    outer_diameter=0.1,
    density_ratio=1.0,
):
    """Factory for creating ConicalGrainSegment instances."""
    return ConicalGrainSegment(
        length=length,
        outer_diameter=outer_diameter,
        upper_core_diameter=0.04,
        lower_core_diameter=0.04,
        density_ratio=density_ratio,
    )


# Parametrize fixtures for FMM2D geometries
fmm2d_geometries = pytest.mark.parametrize(
    "segment_factory,geometry_name",
    [
        (create_star_segment, "Star"),
        (create_wagon_wheel_segment, "WagonWheel"),
        (create_rod_and_tube_segment, "RodAndTube"),
        (create_multi_port_segment, "MultiPort"),
        (create_d_grain_segment, "DGrain"),
    ],
    ids=["Star", "WagonWheel", "RodAndTube", "MultiPort", "DGrain"],
)

# Parametrize fixtures for FMM3D geometries
fmm3d_geometries = pytest.mark.parametrize(
    "segment_factory,geometry_name",
    [
        (create_conical_segment, "Conical"),
    ],
    ids=["Conical"],
)
