import pytest

import machwave.core.compressible_flow.losses as losses_core
import machwave.models.losses as losses


def test_divergence_loss_matches_core(loss_context):
    component = losses.DivergenceLoss()
    assert component.get_loss_fraction(
        loss_context
    ) == losses_core.get_nozzle_divergent_loss_fraction(
        divergent_angle=loss_context.nozzle.divergent_angle
    )
    assert component.target is losses.ThrustCoefficientTermTarget.MOMENTUM


def test_kinetics_loss_matches_core(loss_context):
    component = losses.KineticsLoss()
    assert component.get_loss_fraction(
        loss_context
    ) == losses_core.get_kinetics_loss_fraction(
        i_sp_th_frozen=loss_context.properties.i_sp_frozen,
        i_sp_th_shifting=loss_context.properties.i_sp_shifting,
        chamber_pressure_psi=loss_context.chamber_pressure_psi,
    )
    assert component.target is losses.ThrustCoefficientTermTarget.BOTH


def test_boundary_layer_loss_matches_core(loss_context):
    component = losses.BoundaryLayerLoss()
    assert component.get_loss_fraction(
        loss_context
    ) == losses_core.get_boundary_layer_loss_fraction(
        chamber_pressure_psi=loss_context.chamber_pressure_psi,
        throat_diameter_inch=loss_context.throat_diameter_inch,
        expansion_ratio=loss_context.nozzle.expansion_ratio,
        time=loss_context.time,
        c_1=loss_context.nozzle.c_1,
        c_2=loss_context.nozzle.c_2,
    )


def test_two_phase_flow_loss_matches_core(loss_context):
    component = losses.TwoPhaseFlowLoss()
    assert component.get_loss_fraction(
        loss_context
    ) == losses_core.get_two_phase_flow_loss_fraction(
        chamber_pressure_psi=loss_context.chamber_pressure_psi,
        mass_fraction_of_condensed_phase=loss_context.properties.qsi_chamber,
        expansion_ratio=loss_context.nozzle.expansion_ratio,
        throat_diameter_inch=loss_context.throat_diameter_inch,
        characteristic_length_inch=loss_context.characteristic_length_inch,
    )


def test_context_conversions(loss_context):
    # The context centralizes the psi/inch conversions the formulas need.
    assert loss_context.chamber_pressure_psi == pytest.approx(1015.3, rel=1e-3)
    assert loss_context.throat_diameter_inch == pytest.approx(0.7874, rel=1e-3)
    assert loss_context.characteristic_length_inch > 0.0


def test_constant_fraction_loss_returns_fixed_value(loss_context):
    component = losses.ConstantFractionLoss(0.07, name="other_losses")
    assert component.get_loss_fraction(loss_context) == 0.07
    assert component.name == "other_losses"
    assert component.target is losses.ThrustCoefficientTermTarget.BOTH


def test_constant_fraction_loss_rejects_out_of_range():
    with pytest.raises(ValueError):
        losses.ConstantFractionLoss(1.5, name="x")
