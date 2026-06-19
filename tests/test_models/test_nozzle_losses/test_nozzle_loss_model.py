import pytest

import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.nozzle_losses.components.base as components_base
import machwave.models.propellants as propellants

SOLID = propellants.MixtureType.SOLID
BILIQUID = propellants.MixtureType.BILIQUID


def test_no_loss_model_passes_terms_through(timestep_conditions):
    model = nozzle_losses.presets.no_loss_model(mixture_type=SOLID)
    result = model.evaluate(1.2, 0.3, timestep_conditions)

    assert result.momentum_term == 1.2
    assert result.pressure_term == 0.3
    assert result.nozzle_efficiency == 1.0
    assert result.loss_fractions == {}


def test_constant_efficiency_derates_both_terms(timestep_conditions):
    model = nozzle_losses.presets.constant_efficiency_loss_model(
        0.8, mixture_type=BILIQUID
    )
    result = model.evaluate(1.0, 0.5, timestep_conditions)

    assert result.momentum_term == pytest.approx(0.8)
    assert result.pressure_term == pytest.approx(0.4)
    assert result.nozzle_efficiency == pytest.approx(0.8)


def test_all_both_targets_reduce_to_scalar_correction(timestep_conditions):
    # Every component on BOTH must reproduce the legacy
    # (momentum + pressure) * (1 - sum(fractions)).
    model = nozzle_losses.NozzleLossModel(
        [
            nozzle_losses.components.KineticsLoss(),
            nozzle_losses.components.BoundaryLayerLoss(),
            nozzle_losses.components.TwoPhaseFlowLoss(),
        ],
        mixture_type=SOLID,
    )
    momentum, pressure = 1.4, 0.2
    result = model.evaluate(momentum, pressure, timestep_conditions)
    efficiency = 1.0 - sum(result.loss_fractions.values())

    assert result.momentum_term == pytest.approx(momentum * efficiency)
    assert result.pressure_term == pytest.approx(pressure * efficiency)
    assert result.momentum_term + result.pressure_term == pytest.approx(
        (momentum + pressure) * efficiency
    )
    assert result.nozzle_efficiency == pytest.approx(efficiency)


def test_momentum_only_target_spares_pressure_term(timestep_conditions):
    model = nozzle_losses.NozzleLossModel(
        [
            nozzle_losses.components.DivergentLoss(),
            nozzle_losses.components.KineticsLoss(),
        ],
        mixture_type=SOLID,
    )
    momentum, pressure = 1.0, 1.0
    result = model.evaluate(momentum, pressure, timestep_conditions)
    divergent = result.loss_fractions["divergent_loss"]
    kinetics = result.loss_fractions["kinetics_loss"]

    assert result.momentum_term == pytest.approx(
        momentum * (1.0 - divergent - kinetics)
    )
    assert result.pressure_term == pytest.approx(pressure * (1.0 - kinetics))
    # nozzle_efficiency is the realized corrected-over-ideal ratio, so the
    # momentum-only divergent loss is weighted by the momentum term, not the whole.
    assert result.nozzle_efficiency == pytest.approx(
        (result.momentum_term + result.pressure_term) / (momentum + pressure)
    )


@pytest.mark.parametrize(
    "component_factory",
    [
        nozzle_losses.components.KineticsLoss,
        nozzle_losses.components.BoundaryLayerLoss,
        nozzle_losses.components.TwoPhaseFlowLoss,
    ],
)
def test_rejects_solid_only_component_for_biliquid(component_factory):
    with pytest.raises(ValueError):
        nozzle_losses.NozzleLossModel([component_factory()], mixture_type=BILIQUID)


def test_accepts_divergent_loss_for_biliquid(timestep_conditions):
    model = nozzle_losses.NozzleLossModel(
        [nozzle_losses.components.DivergentLoss()], mixture_type=BILIQUID
    )
    result = model.evaluate(1.0, 1.0, timestep_conditions)
    assert "divergent_loss" in result.loss_fractions


def test_rejects_component_with_empty_name():
    with pytest.raises(ValueError, match="non-empty"):
        nozzle_losses.NozzleLossModel(
            [nozzle_losses.components.ConstantFractionLoss(0.05, name="")],
            mixture_type=SOLID,
        )


def test_rejects_component_with_empty_label():
    with pytest.raises(ValueError, match="non-empty"):
        nozzle_losses.NozzleLossModel(
            [nozzle_losses.components.ConstantFractionLoss(0.05, name="x", label="")],
            mixture_type=SOLID,
        )


def test_rejects_component_missing_name():
    class NamelessLoss(components_base.LossComponent):
        label = "nameless"
        applicable_mixture_types = frozenset({SOLID})
        target = nozzle_losses.ThrustCoefficientTermTarget.BOTH

        @staticmethod
        def loss_fraction() -> float:
            return 0.0

    with pytest.raises(ValueError, match="non-empty"):
        nozzle_losses.NozzleLossModel([NamelessLoss()], mixture_type=SOLID)


def test_rejects_duplicate_component_names():
    with pytest.raises(ValueError):
        nozzle_losses.NozzleLossModel(
            [
                nozzle_losses.components.DivergentLoss(),
                nozzle_losses.components.DivergentLoss(),
            ],
            mixture_type=SOLID,
        )


def test_rejects_losses_derating_below_zero(timestep_conditions):
    model = nozzle_losses.NozzleLossModel(
        [
            nozzle_losses.components.ConstantFractionLoss(0.6, name="a"),
            nozzle_losses.components.ConstantFractionLoss(0.6, name="b"),
        ],
        mixture_type=SOLID,
    )
    with pytest.raises(ValueError):
        model.evaluate(1.0, 1.0, timestep_conditions)


def test_spp1975_solid_model_components():
    model = nozzle_losses.presets.spp1975_solid_loss_model()
    assert model.component_names == [
        "divergent_loss",
        "kinetics_loss",
        "boundary_layer_loss",
        "two_phase_flow_loss",
        "other_losses",
    ]
    assert model.mixture_type is SOLID


def test_constant_plus_divergent_model_components():
    model = nozzle_losses.presets.constant_plus_divergent_efficiency_loss_model(
        mixture_type=BILIQUID
    )
    assert model.component_names == ["constant_efficiency_loss", "divergent_loss"]
    assert model.mixture_type is BILIQUID


def test_constant_efficiency_kwarg_flows_through(timestep_conditions):
    model = nozzle_losses.presets.constant_plus_divergent_efficiency_loss_model(
        efficiency=0.88, mixture_type=BILIQUID
    )
    result = model.evaluate(1.0, 1.0, timestep_conditions)
    assert result.loss_fractions["constant_efficiency_loss"] == pytest.approx(0.12)


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
    boundary_layer,
    divergent,
    kinetics,
    two_phase,
    expected_efficiency,
    timestep_conditions,
):
    model = nozzle_losses.NozzleLossModel(
        [
            nozzle_losses.components.ConstantFractionLoss(
                divergent, name="divergent_loss"
            ),
            nozzle_losses.components.ConstantFractionLoss(
                kinetics, name="kinetics_loss"
            ),
            nozzle_losses.components.ConstantFractionLoss(
                boundary_layer, name="boundary_layer_loss"
            ),
            nozzle_losses.components.ConstantFractionLoss(
                two_phase, name="two_phase_flow_loss"
            ),
        ],
        mixture_type=SOLID,
    )
    result = model.evaluate(1.0, 0.0, timestep_conditions)
    assert result.nozzle_efficiency == pytest.approx(expected_efficiency, abs=1e-3)
