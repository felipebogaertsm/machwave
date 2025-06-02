import pytest

from machwave.core import losses

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.mark.parametrize(
    "divergent_angle, expected_correction_factor",
    [
        (0.0, 0.0),
        (2.0, 0.03),
        (4.0, 0.12),
        (6.0, 0.28),
        (8.0, 0.49),
        (10.0, 0.76),
        (12.0, 1.10),
        (15.0, 1.70),
        (20.0, 3.02),
        (24.0, 4.33),
    ],
)
def test_get_nozzle_divergent_correction_factor(
    divergent_angle, expected_correction_factor
):
    """
    Parameters obtained from Sutton.
    """
    eta_div = losses.get_nozzle_divergent_percentage_loss(
        divergent_angle=divergent_angle
    )
    assert eta_div == pytest.approx(expected_correction_factor, abs=1e-2)


@pytest.mark.parametrize(
    "i_sp_th_frozen, i_sp_th_shifting, chamber_pressure_psi, expected_correction_factor",
    [
        (152.4, 154.1, 150.0, 0.37),  # KNDX @ 150 psi, no pressure damping
        (152.4, 154.1, 200.0, 0.37),  # KNDX @ 200 psi, pressure = threshold
        (152.4, 154.1, 210.0, 0.35),  # KNDX @ 210 psi
        (152.4, 154.1, 1000.0, 0.07),  # KNDX @ 1000 psi
        (250.0, 300.0, 320.0, 3.47),  # large Isp @ 320 psi
        (250.0, 250.0, 200.0, 0.0),  # same frozen/shifting Isp
        (250.0, 250.0, 1000.0, 0.0),  # same frozen/shifting Isp
        (300.0, 300.0, 200.0, 0.0),  # same frozen/shifting Isp
        (300.0, 300.0, 1000.0, 0.0),  # same frozen/shifting Isp
    ],
)
def test_get_kinetics_correction_factor(
    i_sp_th_frozen, i_sp_th_shifting, chamber_pressure_psi, expected_correction_factor
):
    eta_kin = losses.get_kinetics_percentage_loss(
        i_sp_th_frozen=i_sp_th_frozen,
        i_sp_th_shifting=i_sp_th_shifting,
        chamber_pressure_psi=chamber_pressure_psi,
    )
    assert eta_kin == pytest.approx(expected_correction_factor, abs=1e-2)


@pytest.mark.parametrize(
    "chamber_pressure_psi, throat_diam_in, expansion_ratio, time_s, c1, c2, expected_eta_bl",
    [
        # Ordinary nozzle, t = 0 → maximal transient term
        (1000.0, 1.0, 9.0, 0.0, 0.00365, 0.000937, 2.75051564250),
        # Ordinary nozzle, t = 2 s → exponential decay kicks in
        (1000.0, 1.0, 9.0, 2.0, 0.00365, 0.000937, 2.06205742153),
        # Ordinary nozzle, exp. ratio = 15 increases wall area
        (1000.0, 1.0, 15.0, 0.0, 0.00365, 0.000937, 3.01456514418),
        # Steel nozzle, higher pressure, smaller throat; no time dependence
        # because C2 = 0
        (2000.0, 0.5, 12.0, 1.0, 0.00506, 0.000000, 7.99213939195),
        # Steel nozzle, low pressure, large throat, exp. ratio < 9 term reduces factor
        (500.0, 2.0, 8.0, 10.0, 0.00365, 0.000937, 0.72918524795),
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
    eta_bl = losses.get_boundary_layer_percentage_loss(
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
        (200.0, 0.05, 1.0, 10.0, 4.007822978255e-2),
        # Higher condensed-phase fraction (xi ↑)
        (200.0, 0.10, 1.0, 10.0, 5.049540534555e-2),
        # Larger throat diameter (d_throat ↑)
        (200.0, 0.05, 2.0, 10.0, 4.180408656744e-2),
        # Higher chamber pressure (P ↑)
        (1000.0, 0.05, 1.0, 10.0, 6.853280891354e-2),
    ],
)
def test_get_two_phase_phase_loss_particle_size(
    P_psi, xi, d_throat_in, L_c_in, expected_um
):
    size_um = losses._get_two_phase_phase_loss_particle_size(
        chamber_pressure_psi=P_psi,
        xi=xi,
        throat_diameter_inch=d_throat_in,
        characteristic_length_inch=L_c_in,
    )

    assert size_um == pytest.approx(expected_um, abs=1e-6)


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
        (150.0, 0.12, 9.0, 0.8, 20.0, 5.0, 7.7083257633896425),
        # 1 in ≤ throat < 2 in
        (200.0, 0.12, 10.0, 1.5, 20.0, 6.0, 5.081089868159106),
        # throat ≥ 2 in, particle < 4 µm
        (250.0, 0.12, 12.0, 3.0, 20.0, 3.0, 1.6621488765966366),
        # throat ≥ 2 in, 4 µm ≤ particle ≤ 8 µm
        (250.0, 0.12, 12.0, 3.0, 20.0, 6.0, 3.4185173799418895),
        # throat ≥ 2 in, particle > 8 µm
        (250.0, 0.12, 12.0, 3.0, 20.0, 9.0, 3.7947076355546048),
        # --------------------- xi < 0.09 branch ---------------------
        # throat < 1 in
        (150.0, 0.05, 9.0, 0.8, 20.0, 5.0, 3.708669962078615),
        # 1 in ≤ throat < 2 in
        (200.0, 0.05, 10.0, 1.5, 20.0, 6.0, 2.4446405026319503),
        # throat ≥ 2 in, particle < 4 µm
        (250.0, 0.05, 12.0, 3.0, 20.0, 3.0, 0.7967177893556986),
        # throat ≥ 2 in, 4 µm ≤ particle ≤ 8 µm
        (250.0, 0.05, 12.0, 3.0, 20.0, 6.0, 1.644734941282387),
        # throat ≥ 2 in, particle > 8 µm
        (250.0, 0.05, 12.0, 3.0, 20.0, 9.0, 1.820912334005975),
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
        losses,
        "_get_two_phase_phase_loss_particle_size",
        lambda *_a, **_kw: mock_particle_um,
    )

    eta_tp = losses.get_two_phase_flow_percentage_loss(
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
        (2, 3, 4, 5, 0.86),  # typical values
        (25, 25, 25, 25, 0.0),  # lower-bound edge case (sums 1.0)
    ],
)
def test_get_overall_nozzle_efficiency_valid(
    eta_div, eta_kin, eta_bl, eta_2p, expected_eta_noz
):
    """
    Ensures the overall efficiency equals the arithmetic sum and
    respects decorator-enforced [0, 1] bounds.
    """
    eta_total = losses.get_overall_nozzle_efficiency(
        eta_div=eta_div,
        eta_kin=eta_kin,
        eta_bl=eta_bl,
        eta_2p=eta_2p,
        other_losses=0,
    )

    assert eta_total == pytest.approx(expected_eta_noz, abs=1e-12)


def test_get_overall_nozzle_efficiency_out_of_bounds():
    """
    When the sum exceeds 1, the @check_bounds decorator should raise.
    """
    with pytest.raises((ValueError, AssertionError)):
        # Sum = 1.10, outside allowed range.
        losses.get_overall_nozzle_efficiency(
            eta_div=40, eta_kin=30, eta_bl=20, eta_2p=20
        )
