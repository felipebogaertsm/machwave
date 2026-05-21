import numpy as np
import pytest

import machwave.core.structural.bolted_joints as bolted_joints


@pytest.mark.parametrize(
    "load, diameter, n_planes",
    [
        (12_000.0, 5.2e-3, 1),
        (18_500.0, 6.5e-3, 2),
        (25_000.0, 10.0e-3, 1),
    ],
)
def test_shear_stress_per_bolt(load, diameter, n_planes):
    area = np.pi * (diameter / 2.0) ** 2
    expected = load / (n_planes * area)
    result = bolted_joints.get_shear_stress_per_bolt(
        load, diameter, n_shear_planes=n_planes
    )
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "load, t_plate, hole_d",
    [
        (10_000.0, 0.010, 0.006),
        (18_000.0, 0.012, 0.008),
    ],
)
def test_bearing_stress(load, t_plate, hole_d):
    expected = load / (t_plate * hole_d)
    result = bolted_joints.get_bearing_stress(load, t_plate, hole_d)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "load, edge_dist, t_plate",
    [
        (8_000.0, 0.012, 0.010),
        (5_500.0, 0.020, 0.008),
    ],
)
def test_tearout_shear_stress_plate(load, edge_dist, t_plate):
    expected = load / (2.0 * edge_dist * t_plate)
    result = bolted_joints.get_tearout_shear_stress_plate(load, edge_dist, t_plate)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "load, pitch, hole_d, t_plate, n_bolts",
    [
        (22_000.0, 0.025, 0.006, 0.010, 2),
        (12_500.0, 0.030, 0.010, 0.012, 1),
    ],
)
def test_net_section_tension_stress_plate(load, pitch, hole_d, t_plate, n_bolts):
    area_each = (pitch - hole_d) * t_plate
    expected = load / (n_bolts * area_each)
    result = bolted_joints.get_net_section_tension_stress_plate(
        load, pitch, t_plate, hole_d, n_bolts_in_row=n_bolts
    )
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "load, edge_angle_deg, OD, t_wall",
    [
        (7_500.0, 10.0, 0.050, 0.002),
        (9_000.0, 15.0, 0.080, 0.003),
    ],
)
def test_tearout_shear_stress_cylinder(load, edge_angle_deg, OD, t_wall):
    edge_dist = 0.5 * OD * np.deg2rad(edge_angle_deg)
    expected = load / (2.0 * edge_dist * t_wall)
    result = bolted_joints.get_tearout_shear_stress_cylinder(
        load, edge_angle_deg, t_wall, OD
    )
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "load, pitch_angle_deg, OD, t_wall, hole_d, n_bolts",
    [
        (30_000.0, 20.0, 0.050, 0.002, 0.006, 2),
        (14_000.0, 30.0, 0.080, 0.003, 0.010, 1),
    ],
)
def test_net_section_tension_stress_cylinder(
    load, pitch_angle_deg, OD, t_wall, hole_d, n_bolts
):
    pitch = 0.5 * OD * np.deg2rad(pitch_angle_deg)
    area_each = (pitch - hole_d) * t_wall
    expected = load / (n_bolts * area_each)
    result = bolted_joints.get_net_section_tension_stress_cylinder(
        load,
        pitch_angle_deg,
        t_wall,
        hole_d,
        OD,
        n_bolts_in_row=n_bolts,
    )
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "diameter, shear_stress, n_planes",
    [
        (5.2e-3, 160e6, 1),  # 5.2 mm, single shear
        (6.5e-3, 200e6, 2),  # 6.5 mm, double shear
        (10.0e-3, 120e6, 1),  # 10 mm
    ],
)
def test_get_max_shear_load_with_reference_values(diameter, shear_stress, n_planes):
    expected = n_planes * np.pi * (diameter / 2.0) ** 2 * shear_stress
    result = bolted_joints.get_max_shear_load(
        shank_diameter=diameter,
        allowable_shear_stress=shear_stress,
        n_shear_planes=n_planes,
    )

    assert pytest.approx(expected) == result


@pytest.mark.parametrize(
    "thickness, hole_diameter, sigma_b",
    [
        (0.010, 0.006, 250e6),  # 10 mm plate, 6 mm hole
        (0.012, 0.008, 180e6),  # 12 mm plate, 8 mm hole
    ],
)
def test_bearing_load_plate(thickness, hole_diameter, sigma_b):
    expected = thickness * hole_diameter * sigma_b
    result = bolted_joints.get_max_bearing_load(thickness, hole_diameter, sigma_b)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "e, thickness, tau",
    [
        (0.012, 0.010, 150e6),  # 12 mm edge, 10 mm thick
        (0.020, 0.008, 100e6),  # 20 mm edge, 8 mm thick
    ],
)
def test_tearout_load_plate(e, thickness, tau):
    expected = 2.0 * e * thickness * tau
    result = bolted_joints.get_max_tearout_load_plate(e, thickness, tau)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "p, hole_diameter, thickness, n, sigma_t",
    [
        (0.025, 0.006, 0.010, 2, 200e6),  # two bolts, 25 mm pitch
        (0.030, 0.010, 0.012, 1, 160e6),  # one bolt, 30 mm pitch
    ],
)
def test_net_tension_load_plate(p, hole_diameter, thickness, n, sigma_t):
    expected = n * (p - hole_diameter) * thickness * sigma_t
    result = bolted_joints.get_max_net_tension_load_plate(
        p, thickness, hole_diameter, sigma_t, n_bolts_in_row=n
    )
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "angle_deg, outer_diameter, thickness, tau",
    [
        (10.0, 0.050, 0.002, 150e6),  # 10° to edge, 50 mm OD
        (15.0, 0.080, 0.003, 120e6),  # 15° to edge, 80 mm OD
    ],
)
def test_tearout_load_cylinder(angle_deg, outer_diameter, thickness, tau):
    e = 0.5 * outer_diameter * np.deg2rad(angle_deg)
    expected = 2.0 * e * thickness * tau
    result = bolted_joints.get_max_tearout_load_cylinder(
        angle_deg, thickness, outer_diameter, tau
    )
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "pitch_angle_deg, outer_diameter, thickness, hole_diameter, n, sigma_t",
    [
        (20.0, 0.050, 0.002, 0.006, 2, 200e6),  # two bolts 20° apart
        (30.0, 0.080, 0.003, 0.010, 1, 160e6),  # one bolt 30° apart
    ],
)
def test_net_tension_load_cylinder(
    pitch_angle_deg, outer_diameter, thickness, hole_diameter, n, sigma_t
):
    p = 0.5 * outer_diameter * np.deg2rad(pitch_angle_deg)
    expected = n * (p - hole_diameter) * thickness * sigma_t
    result = bolted_joints.get_max_net_tension_load_cylinder(
        pitch_angle_deg,
        thickness,
        hole_diameter,
        sigma_t,
        outer_diameter,
        n_bolts_in_row=n,
    )
    assert result == pytest.approx(expected)
