import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries


def test_star_segment_geometry_validation():
    # Control group:
    _ = grain_geometries.StarGrainSegment(
        outer_diameter=41e-3,
        length=0.5,
        number_of_points=5,
        point_length=15e-3,
        point_width=10e-3,
    )

    # Negative number of points:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=-5,
            point_length=15e-3,
            point_width=10e-3,
        )

    # Too many points:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=13,
            point_length=15e-3,
            point_width=10e-3,
        )

    # Negative point length:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=5,
            point_length=-15e-3,
            point_width=10e-3,
        )

    # Negative point width:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.StarGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            number_of_points=5,
            point_length=15e-3,
            point_width=-10e-3,
        )
