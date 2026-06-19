import pytest

import machwave.core.conversions as conversions
import machwave.models.nozzle_losses.components.spp1975 as spp1975


@pytest.mark.parametrize(
    "i_sp_frozen, i_sp_shifting, chamber_pressure_psi, expected_loss_fraction",
    [
        (152.4, 154.1, 150.0, 0.0037),  # KNDX @ 150 psi, no pressure damping
        (152.4, 154.1, 200.0, 0.0037),  # KNDX @ 200 psi, pressure = threshold
        (152.4, 154.1, 210.0, 0.0035),  # KNDX @ 210 psi
        (152.4, 154.1, 1000.0, 0.0007),  # KNDX @ 1000 psi
        (250.0, 300.0, 320.0, 0.0347),  # large Isp @ 320 psi
        (250.0, 250.0, 200.0, 0.0),  # same frozen/shifting Isp
        (250.0, 250.0, 1000.0, 0.0),  # same frozen/shifting Isp
        (300.0, 300.0, 200.0, 0.0),  # same frozen/shifting Isp
        (300.0, 300.0, 1000.0, 0.0),  # same frozen/shifting Isp
    ],
)
def test_kinetics_loss_fraction(
    i_sp_frozen, i_sp_shifting, chamber_pressure_psi, expected_loss_fraction
):
    kinetics_loss = spp1975.KineticsLoss.loss_fraction(
        i_sp_frozen=i_sp_frozen,
        i_sp_shifting=i_sp_shifting,
        chamber_pressure=conversions.convert_psi_to_pa(chamber_pressure_psi),
    )
    assert kinetics_loss == pytest.approx(expected_loss_fraction, abs=1e-4)


@pytest.mark.parametrize(
    "chamber_pressure_psi, throat_diam_in, expansion_ratio, time_s, c1, c2, expected_loss_fraction",
    [
        # Ordinary nozzle, t = 0, maximal transient term
        (1000.0, 1.0, 9.0, 0.0, 0.00365, 0.000937, 0.0275051564250),
        # Ordinary nozzle, t = 2 s, exponential decay kicks in
        (1000.0, 1.0, 9.0, 2.0, 0.00365, 0.000937, 0.0206205742153),
        # Ordinary nozzle, expansion ratio = 15 increases wall area
        (1000.0, 1.0, 15.0, 0.0, 0.00365, 0.000937, 0.0301456514418),
        # Steel nozzle, higher pressure, smaller throat, C2 = 0
        (2000.0, 0.5, 12.0, 1.0, 0.00506, 0.000000, 0.0799213939195),
        # Steel nozzle, low pressure, large throat, expansion ratio < 9 reduces factor
        (500.0, 2.0, 8.0, 10.0, 0.00365, 0.000937, 0.00729185247950),
    ],
)
def test_boundary_layer_loss_fraction(
    chamber_pressure_psi,
    throat_diam_in,
    expansion_ratio,
    time_s,
    c1,
    c2,
    expected_loss_fraction,
):
    boundary_layer_loss = spp1975.BoundaryLayerLoss.loss_fraction(
        chamber_pressure=conversions.convert_psi_to_pa(chamber_pressure_psi),
        throat_diameter=conversions.convert_inch_to_meter(throat_diam_in),
        expansion_ratio=expansion_ratio,
        time=time_s,
        c_1=c1,
        c_2=c2,
    )

    assert boundary_layer_loss == pytest.approx(expected_loss_fraction, abs=1e-11)


@pytest.mark.parametrize(
    "P_psi, xi, d_throat_in, L_c_in, expected_um",
    [
        # L_c edge cases
        (200.0, 0.05, 1.0, 0.0, 0.0),  # L_c = 0, particle size should be 0
        (200.0, 0.05, 1.0, 1000.0, 1.003407514404),  # Large L_c (saturation)
        # Normal operating regime (L_c = 10 in)
        (200.0, 0.05, 1.0, 10.0, 4.007822978255e-2),  # Baseline
        (200.0, 0.10, 1.0, 10.0, 5.049540534555e-2),  # High condensed phase fraction
        (200.0, 0.05, 2.0, 10.0, 4.180408656744e-2),  # Large throat
        (1000.0, 0.05, 1.0, 10.0, 6.853280891354e-2),  # High chamber pressure
    ],
)
def test_two_phase_average_particle_size(P_psi, xi, d_throat_in, L_c_in, expected_um):
    size_um = spp1975.TwoPhaseFlowLoss._average_particle_size(
        chamber_pressure_psi=P_psi,
        mass_fraction_of_condensed_phase=xi,
        throat_diameter_inch=d_throat_in,
        characteristic_length_inch=L_c_in,
    )

    assert size_um == pytest.approx(expected_um, abs=1e-6)


@pytest.mark.parametrize(
    (
        "chamber_psi",
        "xi",
        "eps",
        "d_throat_in",
        "mock_particle_um",
        "expected_loss_fraction",
    ),
    [
        # - xi >= 0.09 branch
        # throat < 1 in
        (150.0, 0.12, 9.0, 0.8, 5.0, 0.077083257633896425),
        # 1 in <= throat < 2 in
        (200.0, 0.12, 10.0, 1.5, 6.0, 0.05081089868159106),
        # throat >= 2 in, particle < 4 um
        (250.0, 0.12, 12.0, 3.0, 3.0, 0.016621488765966366),
        # throat >= 2 in, 4 um <= particle <= 8 um
        (250.0, 0.12, 12.0, 3.0, 6.0, 0.034185173799418895),
        # throat >= 2 in, particle > 8 um
        (250.0, 0.12, 12.0, 3.0, 9.0, 0.037947076355546048),
        # - xi < 0.09 branch
        # throat < 1 in
        (150.0, 0.05, 9.0, 0.8, 5.0, 0.03708669962078615),
        # 1 in <= throat < 2 in
        (200.0, 0.05, 10.0, 1.5, 6.0, 0.024446405026319503),
        # throat >= 2 in, particle < 4 um
        (250.0, 0.05, 12.0, 3.0, 3.0, 0.007967177893556986),
        # throat >= 2 in, 4 um <= particle <= 8 um
        (250.0, 0.05, 12.0, 3.0, 6.0, 0.01644734941282387),
        # throat >= 2 in, particle > 8 um
        (250.0, 0.05, 12.0, 3.0, 9.0, 0.01820912334005975),
    ],
)
def test_two_phase_flow_loss_fraction(
    monkeypatch,
    chamber_psi,
    xi,
    eps,
    d_throat_in,
    mock_particle_um,
    expected_loss_fraction,
):
    # Patch the private helper to return a controlled particle size; the
    # characteristic length (and thus free_chamber_volume) then does not matter.
    monkeypatch.setattr(
        spp1975.TwoPhaseFlowLoss,
        "_average_particle_size",
        lambda *_a, **_kw: mock_particle_um,
    )

    two_phase_loss = spp1975.TwoPhaseFlowLoss.loss_fraction(
        chamber_pressure=conversions.convert_psi_to_pa(chamber_psi),
        mass_fraction_of_condensed_phase=xi,
        expansion_ratio=eps,
        throat_diameter=conversions.convert_inch_to_meter(d_throat_in),
        free_chamber_volume=1e-3,
    )

    assert two_phase_loss == pytest.approx(expected_loss_fraction, abs=1e-14)
