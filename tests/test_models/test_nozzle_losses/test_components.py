import pytest

import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.nozzle_losses.components.divergent as divergent
import machwave.models.nozzle_losses.components.spp1975 as spp1975


def test_divergence_loss_matches_core(timestep_conditions):
    component = nozzle_losses.components.DivergentLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == divergent.get_divergent_loss_fraction(
        divergent_angle=timestep_conditions.nozzle.divergent_angle
    )
    assert component.target is nozzle_losses.ThrustCoefficientTermTarget.MOMENTUM


def test_kinetics_loss_matches_core(timestep_conditions):
    component = nozzle_losses.components.KineticsLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.get_kinetics_loss_fraction(
        i_sp_th_frozen=timestep_conditions.propellant_properties.i_sp_frozen,
        i_sp_th_shifting=timestep_conditions.propellant_properties.i_sp_shifting,
        chamber_pressure_psi=timestep_conditions.chamber_pressure_psi,
    )
    assert component.target is nozzle_losses.ThrustCoefficientTermTarget.BOTH


def test_boundary_layer_loss_matches_core(timestep_conditions):
    component = nozzle_losses.components.BoundaryLayerLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.get_boundary_layer_loss_fraction(
        chamber_pressure_psi=timestep_conditions.chamber_pressure_psi,
        throat_diameter_inch=timestep_conditions.throat_diameter_inch,
        expansion_ratio=timestep_conditions.nozzle.expansion_ratio,
        time=timestep_conditions.time,
        c_1=timestep_conditions.nozzle.c_1,
        c_2=timestep_conditions.nozzle.c_2,
    )


def test_two_phase_flow_loss_matches_core(timestep_conditions):
    component = nozzle_losses.components.TwoPhaseFlowLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.get_two_phase_flow_loss_fraction(
        chamber_pressure_psi=timestep_conditions.chamber_pressure_psi,
        mass_fraction_of_condensed_phase=timestep_conditions.propellant_properties.qsi_chamber,
        expansion_ratio=timestep_conditions.nozzle.expansion_ratio,
        throat_diameter_inch=timestep_conditions.throat_diameter_inch,
        characteristic_length_inch=timestep_conditions.characteristic_length_inch,
    )


def test_timestep_conditions_conversions(timestep_conditions):
    # The timestep conditions centralize the psi/inch conversions the formulas need.
    assert timestep_conditions.chamber_pressure_psi == pytest.approx(1015.3, rel=1e-3)
    assert timestep_conditions.throat_diameter_inch == pytest.approx(0.7874, rel=1e-3)
    assert timestep_conditions.characteristic_length_inch > 0.0


def test_constant_fraction_loss_returns_fixed_value(timestep_conditions):
    component = nozzle_losses.components.ConstantFractionLoss(0.07, name="other_losses")
    assert component.get_loss_fraction(timestep_conditions) == 0.07
    assert component.name == "other_losses"
    assert component.target is nozzle_losses.ThrustCoefficientTermTarget.BOTH


def test_constant_fraction_loss_rejects_out_of_range():
    with pytest.raises(ValueError):
        nozzle_losses.components.ConstantFractionLoss(1.5, name="x")
