"""
Tests for the finocyl 3D FMM grain segment.

NOTE: As with the other FMM grains, results depend on the map_dim parameter.
The cross-section assertions here compare relative quantities (finned slices
versus unfinned slices) rather than absolute analytical values, since the
finocyl burn area has no simple closed form.
"""

import numpy as np
import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries

# Aft-flush finned section over the lower 40% of the segment. The unfinned
# forward section lets us compare slices with and without fins.
LENGTH = 0.2
OUTER_DIAMETER = 0.1
FINNED_LENGTH = 0.08

VALID_PARAMS = dict(
    length=LENGTH,
    outer_diameter=OUTER_DIAMETER,
    core_diameter=0.03,
    number_of_fins=6,
    fin_length=0.02,
    fin_width=0.006,
    finned_length=FINNED_LENGTH,
    fin_axial_offset=0.0,
)

# Axial positions (z, in meters from the aft end) inside and outside the
# finned band, both away from the end-face slices.
Z_FINNED = 0.04
Z_UNFINNED = 0.15


@pytest.fixture(scope="module")
def finocyl_segment():
    return grain_geometries.FinocylGrainSegment(**VALID_PARAMS)


def test_web_thickness_positive(finocyl_segment):
    assert finocyl_segment.get_web_thickness() > 0


def test_burn_area_is_positive_float(finocyl_segment):
    web_thickness = finocyl_segment.get_web_thickness()

    for web_distance in np.linspace(0, web_thickness * 0.8, 3):
        value = finocyl_segment.get_burn_area(web_distance)
        assert isinstance(value, float), f"Expected float, but got {type(value)}"
        assert value > 0


def test_burn_area_curve_is_smooth_and_non_negative(finocyl_segment):
    """The marching-cubes burn-area curve is smooth and never negative.

    The iso-surface area varies gently with web, so the interpolated curve must
    stay non-negative and have only low high-frequency ripple across the whole
    web (a quantization sawtooth would maximize the second difference).
    """
    segment = finocyl_segment
    web_thickness = segment.get_web_thickness()
    webs = np.linspace(0.0, web_thickness, 60)
    curve = np.array([segment.get_burn_area(w) for w in webs])

    assert np.all(curve >= 0.0)

    second_difference = curve[2:] - 2.0 * curve[1:-1] + curve[:-2]
    ripple = float(np.sqrt(np.mean(second_difference**2)) / np.mean(np.abs(curve)))
    assert ripple < 0.1


def test_port_area_returns_float(finocyl_segment):
    value = finocyl_segment.get_port_area(web_distance=0.0, z=Z_FINNED)
    assert isinstance(value, float), f"Expected float, but got {type(value)}"
    assert value > 0


def test_finned_slice_opens_more_port_area_than_unfinned_slice(finocyl_segment):
    """The fins carve extra material, so a finned slice has a larger port."""
    finned_port = finocyl_segment.get_port_area(web_distance=0.0, z=Z_FINNED)
    unfinned_port = finocyl_segment.get_port_area(web_distance=0.0, z=Z_UNFINNED)

    assert finned_port > unfinned_port


def test_finned_slice_has_less_solid_material_than_unfinned_slice(finocyl_segment):
    """At ignition, a finned cross-section retains fewer solid cells."""
    face_map = finocyl_segment.get_face_map(web_distance=0.0)

    normalized_length = finocyl_segment.get_normalized_length()
    finned_index = int(round(Z_FINNED / LENGTH * (normalized_length - 1)))
    unfinned_index = int(round(Z_UNFINNED / LENGTH * (normalized_length - 1)))

    finned_solid = np.count_nonzero(face_map[finned_index] == 1)
    unfinned_solid = np.count_nonzero(face_map[unfinned_index] == 1)

    assert finned_solid < unfinned_solid


def test_unfinned_slice_matches_plain_core(finocyl_segment):
    """Outside the finned band the port is the plain circular bore."""
    # Compare against a conical segment with a constant (equal-diameter) core.
    # Both are 3D FMM grains, so they share the same discretization bias and a
    # tight tolerance is meaningful (an analytical BATES core would not be).
    plain_bore = grain_geometries.ConicalGrainSegment(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=VALID_PARAMS["core_diameter"],
        lower_core_diameter=VALID_PARAMS["core_diameter"],
    )

    unfinned_port = finocyl_segment.get_port_area(web_distance=0.0, z=Z_UNFINNED)
    expected_port = plain_bore.get_port_area(web_distance=0.0, z=Z_UNFINNED)

    assert unfinned_port == pytest.approx(expected_port, rel=0.05)


def test_default_offset_places_fins_at_aft_end():
    """With the default offset, the finned band sits against the aft (z=0) end."""
    segment = grain_geometries.FinocylGrainSegment(
        **{**VALID_PARAMS, "fin_axial_offset": 0.0}
    )

    aft_port = segment.get_port_area(web_distance=0.0, z=Z_FINNED)
    forward_port = segment.get_port_area(web_distance=0.0, z=Z_UNFINNED)

    assert aft_port > forward_port


def test_transition_tapers_fin_depth():
    """With a transition, the fins are shallower in the ramp than at full depth."""
    segment = grain_geometries.FinocylGrainSegment(
        length=0.2,
        outer_diameter=0.1,
        core_diameter=0.03,
        number_of_fins=6,
        fin_length=0.02,
        fin_width=0.006,
        finned_length=0.1,  # band spans z in [0.05, 0.15]
        fin_axial_offset=0.05,  # centered, both ends meet cylindrical sections
        transition_length=0.03,  # ramps over [0.05, 0.08] and [0.12, 0.15]
    )

    full_depth_port = segment.get_port_area(web_distance=0.0, z=0.10)  # plateau
    transition_port = segment.get_port_area(web_distance=0.0, z=0.065)  # mid-ramp
    cylindrical_port = segment.get_port_area(web_distance=0.0, z=0.02)  # outside band

    assert full_depth_port > transition_port > cylindrical_port


def test_transition_does_not_taper_at_flush_end():
    """A finned section flush with the aft end stays full-depth at that end."""
    segment = grain_geometries.FinocylGrainSegment(
        length=0.2,
        outer_diameter=0.1,
        core_diameter=0.03,
        number_of_fins=6,
        fin_length=0.02,
        fin_width=0.006,
        finned_length=0.1,  # band spans z in [0, 0.1], flush against the aft end
        fin_axial_offset=0.0,
        transition_length=0.03,  # only the forward boundary (z=0.1) ramps
    )

    aft_port = segment.get_port_area(web_distance=0.0, z=0.02)  # flush aft, full depth
    forward_ramp_port = segment.get_port_area(web_distance=0.0, z=0.085)  # forward ramp

    assert aft_port > forward_ramp_port


def test_transition_bound_depends_on_tapering_interfaces():
    """A flush band allows a transition up to the finned length; centered, half of it."""
    # Flush at the aft end: one tapering interface, transition up to finned_length.
    grain_geometries.FinocylGrainSegment(
        **{**VALID_PARAMS, "fin_axial_offset": 0.0, "transition_length": FINNED_LENGTH}
    )

    # Centered: two tapering interfaces, so the same transition no longer fits.
    centered_offset = (LENGTH - FINNED_LENGTH) / 2
    with pytest.raises(grain_models.GrainGeometryError):
        grain_geometries.FinocylGrainSegment(
            **{
                **VALID_PARAMS,
                "fin_axial_offset": centered_offset,
                "transition_length": FINNED_LENGTH,
            }
        )


@pytest.mark.parametrize(
    "overrides",
    [
        dict(core_diameter=0.0),
        dict(core_diameter=0.1),  # equal to outer diameter
        dict(number_of_fins=0),
        dict(number_of_fins=12),  # 12 or more is rejected
        dict(fin_length=0.0),
        dict(fin_width=0.0),
        dict(fin_length=0.04),  # fin tip reaches the casing
        dict(fin_width=0.05),  # fins overlap at their tips
        dict(finned_length=0.0),
        dict(finned_length=0.3),  # exceeds the segment length
        dict(fin_axial_offset=-0.01),
        dict(fin_axial_offset=0.15),  # offset + finned length exceeds length
        dict(transition_length=-0.01),
        dict(transition_length=0.1),  # transition exceeds the finned length
    ],
)
def test_invalid_geometry_raises(overrides):
    with pytest.raises(grain_models.GrainGeometryError):
        grain_geometries.FinocylGrainSegment(**{**VALID_PARAMS, **overrides})
