import pytest

import machwave.core.mass_balance as mass_balance


BASE_KWARGS = {
    "external_pressure": 101_325.0,
    "free_chamber_volume": 1.0e-3,
    "throat_area": 1.0e-4,
    "k": 1.18,
    "R": 320.0,
    "flame_temperature": 2_800.0,
    "nozzle_discharge_coefficient": 0.95,
}


@pytest.mark.parametrize(
    "chamber_pressure, mass_flow_in",
    [
        (5.0e6, 0.5),  # choked
        (
            1.5e5,
            0.05,
        ),  # sub-critical: external_pressure/chamber_pressure above critical
    ],
)
def test_zero_volume_rate_matches_rigid_form(chamber_pressure, mass_flow_in):
    """With V_dot = 0 (default), output must equal the rigid-volume form."""
    explicit = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=mass_flow_in,
        free_chamber_volume_rate=0.0,
        **BASE_KWARGS,
    )
    default = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=mass_flow_in,
        **BASE_KWARGS,
    )
    assert explicit == default


def test_balanced_mass_flow_isolates_volume_term():
    """With m_dot_in = m_dot_out, dP/dt collapses to -P V_dot / V exactly."""
    chamber_pressure = 4.0e6
    (baseline,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=0.0,
        **BASE_KWARGS,
    )
    mass_flow_out = (
        -baseline
        * BASE_KWARGS["free_chamber_volume"]
        / (BASE_KWARGS["R"] * BASE_KWARGS["flame_temperature"])
    )

    free_chamber_volume_rate = 2.5e-5
    (derivative,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=mass_flow_out,
        free_chamber_volume_rate=free_chamber_volume_rate,
        **BASE_KWARGS,
    )

    expected = (
        -chamber_pressure
        * free_chamber_volume_rate
        / BASE_KWARGS["free_chamber_volume"]
    )
    assert derivative == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize(
    "chamber_pressure, mass_flow_in, free_chamber_volume_rate",
    [
        (5.0e6, 0.5, 2.5e-5),
        (5.0e6, 0.5, -1.0e-5),
        (1.5e5, 0.05, 1.0e-6),
    ],
)
def test_volume_term_is_linear_addition(
    chamber_pressure, mass_flow_in, free_chamber_volume_rate
):
    """dP/dt(V_dot) = dP/dt(0) + (-P V_dot / V) to machine precision."""
    (baseline,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=mass_flow_in,
        free_chamber_volume_rate=0.0,
        **BASE_KWARGS,
    )
    (with_rate,) = mass_balance.compute_chamber_pressure_mass_balance(
        chamber_pressure=chamber_pressure,
        mass_flow_in=mass_flow_in,
        free_chamber_volume_rate=free_chamber_volume_rate,
        **BASE_KWARGS,
    )
    expected = (
        baseline
        - chamber_pressure
        * free_chamber_volume_rate
        / BASE_KWARGS["free_chamber_volume"]
    )
    assert with_rate == pytest.approx(expected, rel=1e-12, abs=1e-12)
