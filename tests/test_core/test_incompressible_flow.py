import pytest

import machwave.core.incompressible_flow as incompressible_flow


@pytest.mark.parametrize(
    "discharge_coefficient,area,density,pressure_upstream,pressure_downstream,expected",
    [
        (0.8, 0.001, 1000, 3e5, 1e5, pytest.approx(16.0)),
        (0.9, 0.0005, 1200, 5e5, 1e5, pytest.approx(13.943, rel=1e-3)),
        (0.7, 0.002, 800, 2e5, 2e5, pytest.approx(0.0)),
        (0.85, 0.0001, 1500, 4e5, 2e5, pytest.approx(2.082, rel=1e-3)),
        (0.95, 0.0015, 900, 6e5, 3e5, pytest.approx(33.114, rel=1e-3)),
    ],
)
def test_get_mass_flow_orifice(
    discharge_coefficient,
    area,
    density,
    pressure_upstream,
    pressure_downstream,
    expected,
):
    mass_flow = incompressible_flow.get_mass_flow_orifice(
        discharge_coefficient,
        area,
        density,
        pressure_upstream,
        pressure_downstream,
    )
    assert mass_flow == expected


def test_get_mass_flow_orifice_raises_value_error():
    """ValueError is raised when downstream pressure exceeds upstream pressure."""
    with pytest.raises(
        ValueError, match="Pressure downstream cannot be greater than upstream"
    ):
        incompressible_flow.get_mass_flow_orifice(
            discharge_coefficient=0.8,
            area=0.001,
            density=1000,
            pressure_upstream=1e5,
            pressure_downstream=3e5,  # Higher than upstream
        )
