import pytest

import machwave.models.losses as losses
import machwave.models.propellants as propellants

SOLID = propellants.MixtureType.SOLID
BILIQUID = propellants.MixtureType.BILIQUID
BOTH = losses.ThrustCoefficientTermTarget.BOTH


def test_no_loss_model_passes_terms_through(loss_context):
    model = losses.no_loss_model(mixture_type=SOLID)
    result = model.evaluate(1.2, 0.3, loss_context)

    assert result.momentum_term == 1.2
    assert result.pressure_term == 0.3
    assert result.nozzle_efficiency == 1.0
    assert result.fractions == {}


def test_constant_efficiency_derates_both_terms(loss_context):
    model = losses.constant_efficiency_loss_model(0.8, mixture_type=BILIQUID)
    result = model.evaluate(1.0, 0.5, loss_context)

    assert result.momentum_term == pytest.approx(0.8)
    assert result.pressure_term == pytest.approx(0.4)
    assert result.nozzle_efficiency == pytest.approx(0.8)


def test_all_both_targets_reduce_to_scalar_correction(loss_context):
    # Every component on BOTH must reproduce the legacy
    # (momentum + pressure) * (1 - sum(fractions)).
    model = losses.NozzleLossModel(
        [
            losses.DivergenceLoss(target=BOTH),
            losses.KineticsLoss(),
            losses.BoundaryLayerLoss(),
            losses.TwoPhaseFlowLoss(),
        ],
        mixture_type=SOLID,
    )
    momentum, pressure = 1.4, 0.2
    result = model.evaluate(momentum, pressure, loss_context)
    efficiency = 1.0 - sum(result.fractions.values())

    assert result.momentum_term == pytest.approx(momentum * efficiency)
    assert result.pressure_term == pytest.approx(pressure * efficiency)
    assert result.momentum_term + result.pressure_term == pytest.approx(
        (momentum + pressure) * efficiency
    )
    assert result.nozzle_efficiency == pytest.approx(efficiency)


def test_momentum_only_target_spares_pressure_term(loss_context):
    model = losses.NozzleLossModel(
        [losses.DivergenceLoss(), losses.KineticsLoss()], mixture_type=SOLID
    )
    momentum, pressure = 1.0, 1.0
    result = model.evaluate(momentum, pressure, loss_context)
    divergent = result.fractions["divergent_loss"]
    kinetics = result.fractions["kinetics_loss"]

    assert result.momentum_term == pytest.approx(
        momentum * (1.0 - divergent - kinetics)
    )
    assert result.pressure_term == pytest.approx(pressure * (1.0 - kinetics))


def test_rejects_component_not_applicable_to_mixture():
    with pytest.raises(ValueError):
        losses.NozzleLossModel([losses.BoundaryLayerLoss()], mixture_type=BILIQUID)


def test_rejects_duplicate_component_names():
    with pytest.raises(ValueError):
        losses.NozzleLossModel(
            [losses.DivergenceLoss(), losses.DivergenceLoss()], mixture_type=SOLID
        )


def test_rejects_losses_derating_below_zero(loss_context):
    model = losses.NozzleLossModel(
        [
            losses.ConstantFractionLoss(0.6, name="a"),
            losses.ConstantFractionLoss(0.6, name="b"),
        ],
        mixture_type=SOLID,
    )
    with pytest.raises(ValueError):
        model.evaluate(1.0, 1.0, loss_context)


def test_spp1975_solid_model_components():
    model = losses.spp1975_solid_loss_model()
    assert model.component_names == [
        "divergent_loss",
        "kinetics_loss",
        "boundary_layer_loss",
        "two_phase_loss",
        "other_losses",
    ]
    assert model.mixture_type is SOLID


def test_spp1975_biliquid_model_components():
    model = losses.spp1975_biliquid_loss_model()
    assert model.component_names == ["divergent_loss", "kinetics_loss", "other_losses"]
    assert model.mixture_type is BILIQUID


def test_other_losses_factory_kwarg_flows_through(loss_context):
    model = losses.spp1975_biliquid_loss_model(other_losses=0.12)
    result = model.evaluate(1.0, 1.0, loss_context)
    assert result.fractions["other_losses"] == 0.12


@pytest.mark.parametrize(
    "boundary_layer, divergent, kinetics, two_phase, expected_efficiency",
    [
        # JANNAF / AFRPL-TR-75-36 Table 4-5 (percentages transcribed to fractions).
        (0.015, 0.017, 0.002, 0.021, 0.945),  # A Bates
        (0.020, 0.017, 0.002, 0.020, 0.941),  # B Bates
        (0.017, 0.017, 0.002, 0.012, 0.952),  # A Bates (no fins)
        (0.004, 0.017, 0.003, 0.003, 0.973),  # Antares 1
        (0.009, 0.030, 0.003, 0.021, 0.937),  # Spartan 2
    ],
)
def test_table_4_5_simplified_method(
    boundary_layer, divergent, kinetics, two_phase, expected_efficiency, loss_context
):
    model = losses.NozzleLossModel(
        [
            losses.ConstantFractionLoss(divergent, name="divergent_loss"),
            losses.ConstantFractionLoss(kinetics, name="kinetics_loss"),
            losses.ConstantFractionLoss(boundary_layer, name="boundary_layer_loss"),
            losses.ConstantFractionLoss(two_phase, name="two_phase_loss"),
        ],
        mixture_type=SOLID,
    )
    result = model.evaluate(1.0, 0.0, loss_context)
    assert result.nozzle_efficiency == pytest.approx(expected_efficiency, abs=1e-3)
