"""
Constant-bore conical burn area versus the analytical hollow cylinder.

With inhibited ends the grain is a pure-radial burner whose lateral burning
area is exactly pi * (core + 2 * web) * length. Results depend on map_dim; the
15% tolerance absorbs the marching-squares quantization and the Savitzky-Golay
smoothing, and the sweep stops at 80% web.
"""

import numpy as np
import pytest

import machwave.core.geometric as geometric
import machwave.models.grain as grain_models
from machwave.models.grain.base import InhibitedSurfaces
from tests.factories import BatesSegmentFactory, ConicalGrainSegmentFactory

LENGTH = 68e-3
OUTER_DIAMETER = 41e-3
CORE_DIAMETER = 15e-3
TOLERANCE = 0.15
WEB_DISTANCE_TRAVEL_PERCENTAGE = 0.8
NUMBER_OF_ITERATIONS = 3


@pytest.fixture
def conical_grain_segment_1():
    return ConicalGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
    )


@pytest.fixture
def radial_conical():
    """Constant-bore conical with inhibited ends: a pure-radial hollow cylinder."""
    return ConicalGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
        inhibited_surfaces=InhibitedSurfaces(
            outer_surface=True, upper_end=True, lower_end=True
        ),
    )


@pytest.fixture
def bates_equivalent_1():
    return BatesSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        core_diameter=CORE_DIAMETER,
    )


def test_burn_area(radial_conical):
    web_thickness = radial_conical.get_web_thickness()

    for web_distance in np.linspace(
        0, web_thickness * WEB_DISTANCE_TRAVEL_PERCENTAGE, NUMBER_OF_ITERATIONS
    ):
        value = radial_conical.get_burn_area(web_distance)

        assert isinstance(value, float), f"Expected float, but got {type(value)}"

        expected_value = np.pi * (CORE_DIAMETER + 2 * web_distance) * LENGTH

        assert value == pytest.approx(expected_value, rel=TOLERANCE), (
            f"Expected {expected_value} (rel {TOLERANCE}), got {value} for "
            f"web_distance {web_distance} out of {web_thickness}"
        )


def test_burn_area_includes_end_faces(conical_grain_segment_1, bates_equivalent_1):
    """With exposed ends, the burn area counts the two end faces (core + 2 faces).

    The marching-cubes surface meshes the axial end faces that a per-slice
    perimeter misses, so an uninhibited constant-bore conical matches the full
    BATES burn area, not just its core area.
    """
    conical_initial = conical_grain_segment_1.get_burn_area(0.0)
    bates_initial = bates_equivalent_1.get_burn_area(0.0)  # core + 2 end faces

    assert conical_initial == pytest.approx(bates_initial, rel=TOLERANCE)


def test_port_area(conical_grain_segment_1, bates_equivalent_1):
    value = conical_grain_segment_1.get_port_area(0, 0.01)

    assert isinstance(value, float), f"Expected float, but got {type(value)}"

    expected_value = bates_equivalent_1.get_port_area(0)
    tolerance = expected_value * TOLERANCE * 2

    assert value == pytest.approx(expected_value, abs=tolerance), (
        f"Expected value {expected_value} with tolerance {tolerance}"
    )


def test_axial_burnout_web_is_calibrated_on_the_anisotropic_grid():
    """A short, both-ends-exposed tube burns out axially before radially.

    Its web thickness is then set by the axial half-length, not the radial web.
    That only comes out right if the axial axis of the anisotropic 3D grid is
    calibrated separately from the cross-section; a single scalar dx mis-scales
    it by the length-to-diameter ratio.
    """
    outer_diameter = 41e-3
    bore_diameter = 30e-3
    length = 8e-3  # axial half-length (4 mm) is below the radial web (5.5 mm)

    segment = ConicalGrainSegmentFactory.build(
        length=length,
        outer_diameter=outer_diameter,
        upper_core_diameter=bore_diameter,
        lower_core_diameter=bore_diameter,
    )

    radial_web = (outer_diameter - bore_diameter) / 2
    axial_half_length = length / 2
    assert axial_half_length < radial_web  # the grain is axial-limited by design

    assert segment.get_web_thickness() == pytest.approx(axial_half_length, rel=0.1)


def test_taper_places_lower_diameter_at_the_nozzle_end():
    """An asymmetric cone places the lower (nozzle) core diameter at the aft end.

    The z map runs from 1 at the aft slice to 0 at the forward slice, and
    get_port_area treats z index 0 as the nozzle end. So the larger of the two
    bores below must show up as the larger port area near the nozzle, and the
    smaller bore near the bulkhead -- not the other way around.
    """
    lower_diameter = 30e-3  # nozzle (aft) end, larger bore
    upper_diameter = 8e-3  # bulkhead (forward) end, smaller bore
    segment = ConicalGrainSegmentFactory.build(
        length=68e-3,
        outer_diameter=41e-3,
        upper_core_diameter=upper_diameter,
        lower_core_diameter=lower_diameter,
    )
    length = segment.length

    # Sample just inside each end; the very end slices are inhibited open faces.
    nozzle_port = segment.get_port_area(web_distance=0.0, z=0.05 * length)
    bulkhead_port = segment.get_port_area(web_distance=0.0, z=0.95 * length)

    # At web distance zero the open port is the core bore at that slice.
    lower_bore = geometric.get_circle_area(lower_diameter)
    upper_bore = geometric.get_circle_area(upper_diameter)

    # The larger bore is at the nozzle, the smaller at the bulkhead.
    assert nozzle_port > bulkhead_port

    # Each end's port matches its own core diameter, not the opposite end's.
    assert abs(nozzle_port - lower_bore) < abs(nozzle_port - upper_bore)
    assert abs(bulkhead_port - upper_bore) < abs(bulkhead_port - lower_bore)


def test_segment_too_short_for_axial_map_is_rejected():
    """int(100 * 0.002 / 0.1) == 2 slices -> rejected."""
    with pytest.raises(grain_models.GrainGeometryError):
        ConicalGrainSegmentFactory.build(
            length=2e-3,
            outer_diameter=100e-3,
            upper_core_diameter=15e-3,
            lower_core_diameter=10e-3,
        )


def test_three_axial_slices_is_accepted():
    """int(100 * 0.0035 / 0.1) == 3, the minimum that validates."""
    segment = ConicalGrainSegmentFactory.build(
        length=3.5e-3,
        outer_diameter=100e-3,
        upper_core_diameter=15e-3,
        lower_core_diameter=10e-3,
    )
    assert segment.get_normalized_length() == 3
