import dataclasses
import inspect
import warnings

import pytest

import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.nozzle_losses.components.constant as constant
import machwave.models.nozzle_losses.components.divergent as divergent
import machwave.models.nozzle_losses.components.spp1975 as spp1975
import machwave.models.propellants as propellants
import machwave.models.thrust_chamber as thrust_chamber

BOTH = nozzle_losses.ThrustCoefficientTermTarget.BOTH
SOLID = propellants.MixtureType.SOLID


def test_divergent_loss_resolves_timestep_conditions(timestep_conditions):
    component = divergent.DivergentLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == divergent.DivergentLoss.compute_loss_fraction(
        divergent_angle=timestep_conditions.nozzle.divergent_angle
    )
    assert component.target is nozzle_losses.ThrustCoefficientTermTarget.MOMENTUM


def test_kinetics_loss_resolves_timestep_conditions(timestep_conditions):
    component = spp1975.KineticsLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.KineticsLoss.compute_loss_fraction(
        i_sp_frozen=timestep_conditions.propellant_properties.i_sp_frozen,
        i_sp_shifting=timestep_conditions.propellant_properties.i_sp_shifting,
        chamber_pressure=timestep_conditions.chamber_pressure,
    )
    assert component.target is BOTH


def test_boundary_layer_loss_resolves_timestep_conditions(timestep_conditions):
    component = spp1975.BoundaryLayerLoss(c_1=0.00365, c_2=0.000937)
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.BoundaryLayerLoss.compute_loss_fraction(
        chamber_pressure=timestep_conditions.chamber_pressure,
        throat_diameter=timestep_conditions.nozzle.throat_diameter,
        expansion_ratio=timestep_conditions.nozzle.expansion_ratio,
        time=timestep_conditions.time,
        c_1=0.00365,
        c_2=0.000937,
    )


def test_boundary_layer_loss_defaults_to_thick_walled_steel_coefficients():
    component = spp1975.BoundaryLayerLoss()
    assert component.c_1 == pytest.approx(0.00506, rel=1e-3)
    assert component.c_2 == pytest.approx(0.0, abs=1e-9)


def test_two_phase_flow_loss_resolves_timestep_conditions(timestep_conditions):
    component = spp1975.TwoPhaseFlowLoss()
    assert component.get_loss_fraction(
        timestep_conditions
    ) == spp1975.TwoPhaseFlowLoss.compute_loss_fraction(
        chamber_pressure=timestep_conditions.chamber_pressure,
        mass_fraction_of_condensed_phase=(
            timestep_conditions.propellant_properties.qsi_chamber
        ),
        expansion_ratio=timestep_conditions.nozzle.expansion_ratio,
        throat_diameter=timestep_conditions.nozzle.throat_diameter,
        free_chamber_volume=timestep_conditions.free_chamber_volume,
    )


def test_component_labels():
    assert divergent.DivergentLoss().label == "divergent nozzle loss"
    assert spp1975.KineticsLoss().label == "kinetics loss"
    assert spp1975.BoundaryLayerLoss().label == "boundary layer loss"
    assert spp1975.TwoPhaseFlowLoss().label == "two-phase flow loss"


def test_constant_fraction_loss_returns_fixed_value(timestep_conditions):
    component = constant.ConstantFractionLoss(0.07, name="other_losses")
    assert component.get_loss_fraction(timestep_conditions) == 0.07
    assert component.name == "other_losses"
    assert component.label == "other losses"
    assert component.target is BOTH


def test_constant_fraction_loss_custom_label():
    component = constant.ConstantFractionLoss(
        0.05, name="other_losses", label="other nozzle losses"
    )
    assert component.label == "other nozzle losses"


def test_constant_fraction_loss_rejects_out_of_range():
    with pytest.raises(ValueError):
        constant.ConstantFractionLoss(1.5, name="x")


def test_get_loss_fraction_rejects_out_of_range(timestep_conditions):
    class OutOfRangeLoss(components_base.LossComponent):
        name = "out_of_range"
        label = "out of range"
        applicable_mixture_types = frozenset({SOLID})
        target = BOTH

        @staticmethod
        def compute_loss_fraction() -> float:
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
        def compute_loss_fraction() -> float:
            return 0.5

    with pytest.warns(UserWarning, match="typical"):
        NarrowRangeLoss().get_loss_fraction(timestep_conditions)


def test_loss_fraction_inside_typical_range_does_not_warn(timestep_conditions):
    # The fixture's 15 deg half-angle gives ~0.017, inside DivergentLoss's range.
    component = divergent.DivergentLoss()
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        component.get_loss_fraction(timestep_conditions)


def test_subclass_missing_loss_fraction_is_rejected():
    with pytest.raises(TypeError, match="compute_loss_fraction"):

        class MissingLossFraction(components_base.LossComponent):
            name = "missing"
            label = "missing"
            applicable_mixture_types = frozenset({SOLID})
            target = BOTH


def test_subclass_non_static_loss_fraction_is_rejected():
    with pytest.raises(TypeError, match="static or class method"):

        class InstanceMethodLoss(components_base.LossComponent):
            name = "instance_method"
            label = "instance method"
            applicable_mixture_types = frozenset({SOLID})
            target = BOTH

            def compute_loss_fraction(self) -> float:
                return 0.0


def test_subclass_missing_target_is_rejected():
    with pytest.raises(TypeError, match="target"):

        class MissingTarget(components_base.LossComponent):
            name = "missing_target"
            label = "missing target"
            applicable_mixture_types = frozenset({SOLID})

            @staticmethod
            def compute_loss_fraction() -> float:
                return 0.0


def test_typical_range_warning_omits_fraction_value(timestep_conditions):
    class NarrowRangeLoss(components_base.LossComponent):
        name = "narrow_range"
        label = "narrow range"
        applicable_mixture_types = frozenset({SOLID})
        target = BOTH
        typical_range = (0.0, 0.01)

        @staticmethod
        def compute_loss_fraction() -> float:
            return 0.5

    with pytest.warns(UserWarning) as record:
        NarrowRangeLoss().get_loss_fraction(timestep_conditions)

    message = str(record[0].message)
    assert "0.5" not in message  # the per-call value is gone so warnings dedup
    assert "[0.0, 0.01]" in message  # the constant bounds stay for context


def test_typical_range_warning_deduplicates_across_drifting_fractions(
    timestep_conditions,
):
    class DriftingLoss(components_base.LossComponent):
        name = "drifting"
        label = "drifting"
        applicable_mixture_types = frozenset({SOLID})
        target = BOTH
        typical_range = (0.0, 0.01)
        timestep_parameter_map = {"chamber_pressure": "chamber_pressure"}

        @staticmethod
        def compute_loss_fraction(chamber_pressure: float) -> float:
            return min(0.5, chamber_pressure / 1.0e8)

    component = DriftingLoss()
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("default", UserWarning)
        for chamber_pressure in (7.0e6, 8.0e6, 9.0e6, 7.0e6):
            component.get_loss_fraction(
                dataclasses.replace(
                    timestep_conditions, chamber_pressure=chamber_pressure
                )
            )

    # Distinct fractions used to produce distinct messages; now one per component.
    assert len(recorded) == 1


def _replace_properties(conditions, **changes):
    return dataclasses.replace(
        conditions,
        propellant_properties=dataclasses.replace(
            conditions.propellant_properties, **changes
        ),
    )


@pytest.mark.parametrize(
    "component, make_conditions",
    [
        (
            spp1975.KineticsLoss(),
            lambda c: _replace_properties(c, i_sp_frozen=250.0, i_sp_shifting=250.0),
        ),
        (
            spp1975.BoundaryLayerLoss(),
            lambda c: dataclasses.replace(c, chamber_pressure=2.0e7),
        ),
        (
            spp1975.TwoPhaseFlowLoss(),
            lambda c: dataclasses.replace(
                _replace_properties(c, qsi_chamber=0.45), free_chamber_volume=5.0e-2
            ),
        ),
    ],
    ids=["kinetics", "boundary_layer", "two_phase"],
)
def test_real_component_warns_outside_typical_range(
    component, make_conditions, timestep_conditions
):
    with pytest.warns(UserWarning, match="typical"):
        component.get_loss_fraction(make_conditions(timestep_conditions))


def test_divergent_loss_warns_outside_typical_range(timestep_conditions):
    base = timestep_conditions.nozzle
    wide_nozzle = thrust_chamber.Nozzle(
        inlet_diameter=base.inlet_diameter,
        throat_diameter=base.throat_diameter,
        divergent_angle=30.0,  # ~0.067 fraction, above the 0.05 upper bound
        convergent_angle=base.convergent_angle,
        expansion_ratio=base.expansion_ratio,
        discharge_coefficient=base.discharge_coefficient,
        separation_pressure_ratio=base.separation_pressure_ratio,
    )
    conditions = dataclasses.replace(timestep_conditions, nozzle=wide_nozzle)
    with pytest.warns(UserWarning, match="typical"):
        divergent.DivergentLoss().get_loss_fraction(conditions)


def test_divergent_loss_warns_below_typical_range(timestep_conditions):
    base = timestep_conditions.nozzle
    narrow_nozzle = thrust_chamber.Nozzle(
        inlet_diameter=base.inlet_diameter,
        throat_diameter=base.throat_diameter,
        divergent_angle=5.0,  # ~0.0019 fraction, below the 0.0075 lower bound
        convergent_angle=base.convergent_angle,
        expansion_ratio=base.expansion_ratio,
        discharge_coefficient=base.discharge_coefficient,
        separation_pressure_ratio=base.separation_pressure_ratio,
    )
    conditions = dataclasses.replace(timestep_conditions, nozzle=narrow_nozzle)
    with pytest.warns(UserWarning, match="typical"):
        divergent.DivergentLoss().get_loss_fraction(conditions)


@pytest.mark.parametrize(
    "component_class",
    [
        constant.ConstantFractionLoss,
        divergent.DivergentLoss,
        spp1975.KineticsLoss,
        spp1975.BoundaryLayerLoss,
        spp1975.TwoPhaseFlowLoss,
    ],
)
def test_loss_fraction_is_static_on_every_component(component_class):
    assert isinstance(
        inspect.getattr_static(component_class, "compute_loss_fraction"), staticmethod
    )


def test_constant_fraction_loss_static_call():
    # The constant shares the physics components' pure static-call contract.
    assert constant.ConstantFractionLoss.compute_loss_fraction(0.07) == 0.07
