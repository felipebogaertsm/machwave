"""
Finocyl 3D FMM grain validated against a CAD model.

The reference burn area, volume, center of gravity, moment of inertia and aft end face
area below were evaluated in SolidWorks 2024.
"""

import numpy as np
import pytest

import machwave.models.grain.geometries as grain_geometries

GEOMETRIC_PARAMS = dict(
    length=0.3048,  # 12 in
    outer_diameter=0.1016,  # 4 in
    core_diameter=0.03556,  # 1.4 in
    number_of_fins=6,
    fin_length=0.0127,  # 0.5 in
    fin_width=0.00635,  # 1/4 in
    finned_length=0.127,  # 5 in, includes the transition
    transition_length=0.0254,  # 1 in
    fin_axial_offset=0.0,  # fins flush against the aft end
)

CASES = [  # only includes web distance of 0.0 mm (initial)
    pytest.param(
        dict(
            web=0.0,
            burn_area=65738.2e-6,
            burn_rel=0.01,
            volume=2112634.15e-9,
            volume_rel=0.01,
            cog_axial=154.91e-3,
            cog_rel=0.005,
            moi_ratio=17763076.55 / 3108025.60,
            moi_rel=0.01,
            end_face=6626.69e-6,
            # The bore annulus less six rectangular fin slots comes to 6626.6 mm^2,
            # matching the CAD cross-section, and the traced slice stays within 0.4%
            # of it at grid resolutions 100 through 200.
            end_face_rel=0.01,
        ),
        id="web=0",
    ),
]


@pytest.fixture(scope="module")
def segment():
    return grain_geometries.FinocylGrainSegment(**GEOMETRIC_PARAMS)


@pytest.mark.parametrize("case", CASES)
def test_burn_area_matches_solidworks(segment, case):
    assert segment.get_burn_area(case["web"]) == pytest.approx(
        case["burn_area"], rel=case["burn_rel"]
    )


@pytest.mark.parametrize("case", CASES)
def test_volume_matches_solidworks(segment, case):
    assert segment.get_volume(case["web"]) == pytest.approx(
        case["volume"], rel=case["volume_rel"]
    )


@pytest.mark.parametrize("case", CASES)
def test_axial_center_of_gravity_matches_solidworks(segment, case):
    cog = segment.get_center_of_gravity(case["web"])
    assert cog[0] == pytest.approx(case["cog_axial"], rel=case["cog_rel"])


@pytest.mark.parametrize("case", CASES)
def test_center_of_gravity_is_on_the_axis(segment, case):
    """Six evenly spaced fins are radially symmetric, so the transverse center of
    gravity stays on the axis."""
    cog = segment.get_center_of_gravity(case["web"])
    pixel = segment.cells_to_meters(1.0)
    assert abs(cog[1]) < pixel
    assert abs(cog[2]) < pixel


@pytest.mark.parametrize("case", CASES)
def test_moment_of_inertia_ratio_matches_solidworks(segment, case):
    """Absolute moments need the SolidWorks propellant density, so the ratio is used
    since it does not depend on the density."""
    diagonal = np.sort(np.diag(segment.get_moment_of_inertia(1800.0, case["web"])))
    axial, transverse = diagonal[0], np.mean(diagonal[1:])
    assert transverse / axial == pytest.approx(case["moi_ratio"], rel=case["moi_rel"])


@pytest.mark.parametrize("case", CASES)
def test_finned_end_face_area_matches_solidworks(segment, case):
    face_map = segment.get_face_map(web_distance=case["web"])
    pixel_area = segment.cells_to_meters(1.0) ** 2
    slice_areas = np.count_nonzero(face_map == 1, axis=(1, 2)) * pixel_area
    end_face = slice_areas[slice_areas > 0.5 * slice_areas.max()][0]
    assert end_face == pytest.approx(case["end_face"], rel=case["end_face_rel"])
