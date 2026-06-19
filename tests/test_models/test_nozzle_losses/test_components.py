import warnings

import pytest

import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.nozzle_losses.components.divergent as divergent
import machwave.models.nozzle_losses.components.spp1975 as spp1975
import machwave.models.propellants as propellants

BOTH = nozzle_losses.ThrustCoefficientTermTarget.BOTH
SOLID = propellants.MixtureType.SOLID


def test_divergent_loss_resolves_timestep_conditions(timestep_conditions):
    component = nozzle_losses.components.DivergentLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == divergent.DivergentLoss.loss_fraction(
        divergent_angle=timestep_conditions.nozzle.divergent_angle
    )
    assert component.target is nozzle_losses.ThrustCoefficientTermTarget.MOMENTUM


def test_kinetics_loss_resolves_timestep_conditions(timestep_conditions):
    component = nozzle_losses.components.KineticsLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.KineticsLoss.loss_fraction(
        i_sp_frozen=timestep_conditions.propellant_properties.i_sp_frozen,
        i_sp_shifting=timestep_conditions.propellant_properties.i_sp_shifting,
        chamber_pressure=timestep_conditions.chamber_pressure,
    )
    assert component.target is BOTH


def test_boundary_layer_loss_resolves_timestep_conditions(timestep_conditions):
    component = nozzle_losses.components.BoundaryLayerLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.BoundaryLayerLoss.loss_fraction(
        chamber_pressure=timestep_conditions.chamber_pressure,
        throat_diameter=timestep_conditions.nozzle.throat_diameter,
        expansion_ratio=timestep_conditions.nozzle.expansion_ratio,
        time=timestep_conditions.time,
        c_1=timestep_conditions.nozzle.c_1,
        c_2=timestep_conditions.nozzle.c_2,
    )


def test_two_phase_flow_loss_resolves_timestep_conditions(timestep_conditions):
    component = nozzle_losses.components.TwoPhaseFlowLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.TwoPhaseFlowLoss.loss_fraction(
        chamber_pressure=timestep_conditions.chamber_pressure,
        mass_fraction_of_condensed_phase=(
            timestep_conditions.propellant_properties.qsi_chamber
        ),
        expansion_ratio=timestep_conditions.nozzle.expansion_ratio,
        throat_diameter=timestep_conditions.nozzle.throat_diameter,
        free_chamber_volume=timestep_conditions.free_chamber_volume,
    )


def test_component_labels():
    assert nozzle_losses.components.DivergentLoss().label == "divergent nozzle loss"
    assert nozzle_losses.components.KineticsLoss().label == "kinetics loss"
    assert nozzle_losses.components.BoundaryLayerLoss().label == "boundary layer loss"
    assert nozzle_losses.components.TwoPhaseFlowLoss().label == "two-phase flow loss"


def test_constant_fraction_loss_returns_fixed_value(timestep_conditions):
    component = nozzle_losses.components.ConstantFractionLoss(0.07, name="other_losses")
    assert component.get_loss_fraction(timestep_conditions) == 0.07
    assert component.name == "other_losses"
    assert component.label == "other losses"
    assert component.target is BOTH


def test_constant_fraction_loss_custom_label():
    component = nozzle_losses.components.ConstantFractionLoss(
        0.05, name="other_losses", label="other nozzle losses"
    )
    assert component.label == "other nozzle losses"


def test_constant_fraction_loss_rejects_out_of_range():
    with pytest.raises(ValueError):
        nozzle_losses.components.ConstantFractionLoss(1.5, name="x")


def test_get_loss_fraction_rejects_out_of_range(timestep_conditions):
    class OutOfRangeLoss(components_base.LossComponent):
        name = "out_of_range"
        label = "out of range"
        applicable_mixture_types = frozenset({SOLID})
        target = BOTH

        @staticmethod
        def loss_fraction() -> float:
            return 1.5

    with pytest.raises(ValueError, match="outside"):
        OutOfRangeLoss().get_loss_fraction(timestep_conditions)


def test_loss_fraction_outside_typical_range_warns(timestep_conditions):
    class NarrowRangeLoss(components_base.LossComponent):
        name = "narrow_range"
        label = "narrow range"
        applicable_mixture_types = frozenset({SOLID})
        target = BOTH
        typical_range = (0.0, 0.01)

        @staticmethod
        def loss_fraction() -> float:
            return 0.5

    with pytest.warns(UserWarning, match="typical"):
        NarrowRangeLoss().get_loss_fraction(timestep_conditions)


def test_loss_fraction_inside_typical_range_does_not_warn(timestep_conditions):
    # The fixture's 15 deg half-angle gives ~0.017, inside DivergentLoss's range.
    component = nozzle_losses.components.DivergentLoss()
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        component.get_loss_fraction(timestep_conditions)


def test_subclass_missing_loss_fraction_is_rejected():
    with pytest.raises(TypeError, match="loss_fraction"):

        class MissingLossFraction(components_base.LossComponent):
            name = "missing"
            label = "missing"
            applicable_mixture_types = frozenset({SOLID})
            target = BOTH


def test_subclass_missing_target_is_rejected():
    with pytest.raises(TypeError, match="target"):

        class MissingTarget(components_base.LossComponent):
            name = "missing_target"
            label = "missing target"
            applicable_mixture_types = frozenset({SOLID})

            @staticmethod
            def loss_fraction() -> float:
                return 0.0
