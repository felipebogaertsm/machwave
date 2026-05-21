import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries


def test_star_segment_geometry_validation():
    # Control group:
    _ = grain_geometries.WagonWheelGrainSegment(
        outer_diameter=41e-3,
        length=0.5,
        core_diameter=8e-3,
        number_of_ports=6,
        port_inner_diameter=15e-3,
        port_outer_diameter=35e-3,
        port_angular_width=45,
    )

    # Negative core diameter:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=-8e-3,
            number_of_ports=-1,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
        )

    # Port inner diameter smaller than core diameter:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=-1,
            port_inner_diameter=7e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
        )

    # Port outer diameter smaller than inner diameter:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=-1,
            port_inner_diameter=15e-3,
            port_outer_diameter=12e-3,
            port_angular_width=45,
        )

    # Negative number of ports:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=-1,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
        )

    # Too many points:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=13,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=45,
        )

    # Negative port angle:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=6,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=-1,
        )

    # Port angle too large:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.WagonWheelGrainSegment(
            outer_diameter=41e-3,
            length=0.5,
            core_diameter=8e-3,
            number_of_ports=6,
            port_inner_diameter=15e-3,
            port_outer_diameter=35e-3,
            port_angular_width=61,
        )
