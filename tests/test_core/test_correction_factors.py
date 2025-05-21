import pytest

from machwave.core import correction_factors


@pytest.mark.parametrize(
    "divergent_angle, expected_correction_factor",
    [
        (0.0, 0.0),
        (2.0, 0.0003),
        (4.0, 0.0012),
        (6.0, 0.0028),
        (8.0, 0.0049),
        (10.0, 0.0076),
        (12.0, 0.0110),
        (15.0, 0.0170),
        (20.0, 0.0302),
        (24.0, 0.0433),
    ],
)
def test_get_nozzle_divergent_correction_factor(
    divergent_angle, expected_correction_factor
):
    """
    Parameters obtained from Sutton.
    """
    eta_div = correction_factors.get_nozzle_divergent_correction_factor(
        divergent_angle=divergent_angle
    )
    assert eta_div == pytest.approx(expected_correction_factor, abs=1e-4)


@pytest.mark.parametrize(
    "i_sp_th_frozen, i_sp_th_shifting, chamber_pressure_psi, expected_correction_factor",
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
def test_get_kinetics_correction_factor(
    i_sp_th_frozen, i_sp_th_shifting, chamber_pressure_psi, expected_correction_factor
):
    eta_kin = correction_factors.get_kinetics_correction_factor(
        i_sp_th_frozen=i_sp_th_frozen,
        i_sp_th_shifting=i_sp_th_shifting,
        chamber_pressure_psi=chamber_pressure_psi,
    )
    assert eta_kin == pytest.approx(expected_correction_factor, abs=1e-4)


@pytest.mark.parametrize(
    "chamber_pressure_psi, throat_diam_in, expansion_ratio, time_s, c1, c2, expected_eta_bl",
    [
        # Ordinary nozzle, t = 0 → maximal transient term
        (1000.0, 1.0, 9.0, 0.0, 0.00365, 0.000937, 0.0275051564250),
        # Ordinary nozzle, t = 2 s → exponential decay kicks in
        (1000.0, 1.0, 9.0, 2.0, 0.00365, 0.000937, 0.0206205742153),
        # Ordinary nozzle, exp. ratio = 15 increases wall area
        (1000.0, 1.0, 15.0, 0.0, 0.00365, 0.000937, 0.0301456514418),
        # Steel nozzle, higher pressure, smaller throat; no time dependence
        # because C2 = 0
        (2000.0, 0.5, 12.0, 1.0, 0.00506, 0.000000, 0.0799213939195),
        # Steel nozzle, low pressure, large throat, exp. ratio < 9 term reduces factor
        (500.0, 2.0, 8.0, 10.0, 0.00365, 0.000937, 0.0072918524795),
    ],
)
def test_get_boundary_layer_correction_factor(
    chamber_pressure_psi,
    throat_diam_in,
    expansion_ratio,
    time_s,
    c1,
    c2,
    expected_eta_bl,
):
    eta_bl = correction_factors.get_boundary_layer_correction_factor(
        chamber_pressure_psi=chamber_pressure_psi,
        throat_diameter_inch=throat_diam_in,
        expansion_ratio=expansion_ratio,
        time=time_s,
        c_1=c1,
        c_2=c2,
    )

    assert eta_bl == pytest.approx(expected_eta_bl, abs=1e-9)


@pytest.mark.parametrize(
    "P_psi, xi, d_throat_in, L_c_in, expected_um",
    [
        # -------- Characteristic-length edge cases -------
        # L_c = 0 → (1 − e⁻ᵏL) term → 0 ⇒ particle size must be 0
        (200.0, 0.05, 1.0, 0.0, 0.0),
        # Large L_c → (1 − e⁻ᵏL) → 1 (saturation)
        (200.0, 0.05, 1.0, 1000.0, 1.003407514404),
        # ----- Normal operating regime (L_c = 10 in) -----
        # Baseline
        (200.0, 0.05, 1.0, 10.0, 4.007822978255e-02),
        # Higher condensed-phase fraction (xi ↑)
        (200.0, 0.10, 1.0, 10.0, 5.049540534555e-02),
        # Larger throat diameter (d_throat ↑)
        (200.0, 0.05, 2.0, 10.0, 4.180408656744e-02),
        # Higher chamber pressure (P ↑)
        (1000.0, 0.05, 1.0, 10.0, 6.853280891354e-02),
    ],
)
def test_get_two_phase_phase_loss_particle_size(
    P_psi, xi, d_throat_in, L_c_in, expected_um
):
    size_um = correction_factors._get_two_phase_phase_loss_particle_size(
        chamber_pressure_psi=P_psi,
        xi=xi,
        throat_diameter_inch=d_throat_in,
        characteristic_length_inch=L_c_in,
    )

    assert size_um == pytest.approx(expected_um, abs=1e-12)


@pytest.mark.parametrize(
    (
        "chamber_psi",
        "xi",  # mole fraction of condensed phase
        "eps",  # expansion ratio
        "d_throat_in",  # throat diameter (in)
        "l_char_in",  # characteristic length (in) – unused after patch
        "mock_particle_um",  # particle size returned by patched helper
        "expected_eta_tp",  # pre-calculated expected result
    ),
    [
        # --------------------- xi ≥ 0.09 branch ---------------------
        # throat < 1 in
        (150.0, 0.12, 9.0, 0.8, 20.0, 5.0, 0.013351211863483013),
        # 1 in ≤ throat < 2 in
        (200.0, 0.12, 10.0, 1.5, 20.0, 6.0, 0.008800705809475019),
        # throat ≥ 2 in, particle < 4 µm
        (250.0, 0.12, 12.0, 3.0, 20.0, 3.0, 0.002878926304008907),
        # throat ≥ 2 in, 4 µm ≤ particle ≤ 8 µm
        (250.0, 0.12, 12.0, 3.0, 20.0, 6.0, 0.005921045788616592),
        # throat ≥ 2 in, particle > 8 µm
        (250.0, 0.12, 12.0, 3.0, 20.0, 9.0, 0.006572626424650138),
        # --------------------- xi < 0.09 branch ---------------------
        # throat < 1 in
        (150.0, 0.05, 9.0, 0.8, 20.0, 5.0, 0.03708669962078615),
        # 1 in ≤ throat < 2 in
        (200.0, 0.05, 10.0, 1.5, 20.0, 6.0, 0.024446405026319503),
        # throat ≥ 2 in, particle < 4 µm
        (250.0, 0.05, 12.0, 3.0, 20.0, 3.0, 0.007967177893556986),
        # throat ≥ 2 in, 4 µm ≤ particle ≤ 8 µm
        (250.0, 0.05, 12.0, 3.0, 20.0, 6.0, 0.01644734941282387),
        # throat ≥ 2 in, particle > 8 µm
        (250.0, 0.05, 12.0, 3.0, 20.0, 9.0, 0.01820912334005975),
    ],
)
def test_get_two_phase_flow_correction_factor(
    monkeypatch,
    chamber_psi,
    xi,
    eps,
    d_throat_in,
    l_char_in,
    mock_particle_um,
    expected_eta_tp,
):
    # Patch the private helper to return a controlled particle size.
    monkeypatch.setattr(
        correction_factors,
        "_get_two_phase_phase_loss_particle_size",
        lambda *_a, **_kw: mock_particle_um,
    )

    eta_tp = correction_factors.get_two_phase_flow_correction_factor(
        chamber_pressure_psi=chamber_psi,
        mole_fraction_of_condensed_phase=xi,
        expansion_ratio=eps,
        throat_diameter_inch=d_throat_in,
        characteristic_length_inch=l_char_in,  # value irrelevant after patch
    )

    assert eta_tp == pytest.approx(expected_eta_tp, abs=1e-12)


@pytest.mark.parametrize(
    "eta_div, eta_kin, eta_bl, eta_2p, expected_eta_noz",
    [
        (0.0, 0.0, 0.0, 0.0, 1.0),  # all zero → upper-bound edge case
        (0.02, 0.03, 0.04, 0.05, 0.86),  # typical values
        (0.25, 0.25, 0.25, 0.25, 0.0),  # lower-bound edge case (sums 1.0)
    ],
)
def test_get_overall_nozzle_efficiency_valid(
    eta_div, eta_kin, eta_bl, eta_2p, expected_eta_noz
):
    """
    Ensures the overall efficiency equals the arithmetic sum and
    respects decorator-enforced [0, 1] bounds.
    """
    eta_total = correction_factors.get_overall_nozzle_efficiency(
        eta_div=eta_div,
        eta_kin=eta_kin,
        eta_bl=eta_bl,
        eta_2p=eta_2p,
    )

    assert eta_total == pytest.approx(expected_eta_noz, abs=1e-12)


def test_get_overall_nozzle_efficiency_out_of_bounds():
    """
    When the sum exceeds 1, the @check_bounds decorator should raise.
    """
    with pytest.raises((ValueError, AssertionError)):
        # Sum = 1.10, outside allowed range.
        correction_factors.get_overall_nozzle_efficiency(
            eta_div=0.4, eta_kin=0.3, eta_bl=0.2, eta_2p=0.2
        )
