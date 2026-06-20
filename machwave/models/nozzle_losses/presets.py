import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components as losses_components
import machwave.models.propellants as propellants

_SOLID = propellants.MixtureType.SOLID
_CONSTANT_EFFICIENCY_LOSS_NAME = "constant_efficiency_loss"

DEFAULT_OTHER_LOSSES = 0.05
DEFAULT_NOZZLE_EFFICIENCY = 0.85


def spp1975_solid_loss_model(
    *, other_losses: float = DEFAULT_OTHER_LOSSES
) -> losses_base.NozzleLossModel:
    """Solid Performance Program 1975 nozzle loss set."""
    return losses_base.NozzleLossModel(
        [
            losses_components.DivergentLoss(),
            losses_components.KineticsLoss(),
            losses_components.BoundaryLayerLoss(),
            losses_components.TwoPhaseFlowLoss(),
            losses_components.ConstantFractionLoss(other_losses, name="other_losses"),
        ],
        mixture_type=_SOLID,
    )


def constant_efficiency_loss_model(
    efficiency: float, *, mixture_type: propellants.MixtureType
) -> losses_base.NozzleLossModel:
    """A flat nozzle efficiency applied to the whole thrust coefficient."""
    return losses_base.NozzleLossModel(
        [
            losses_components.ConstantFractionLoss(
                1.0 - efficiency, name=_CONSTANT_EFFICIENCY_LOSS_NAME
            )
        ],
        mixture_type=mixture_type,
    )


def constant_plus_divergent_efficiency_loss_model(
    efficiency: float = DEFAULT_NOZZLE_EFFICIENCY,
    *,
    mixture_type: propellants.MixtureType,
) -> losses_base.NozzleLossModel:
    """A flat efficiency plus the geometric nozzle divergence loss."""
    return losses_base.NozzleLossModel(
        [
            losses_components.ConstantFractionLoss(
                1.0 - efficiency, name=_CONSTANT_EFFICIENCY_LOSS_NAME
            ),
            losses_components.DivergentLoss(),
        ],
        mixture_type=mixture_type,
    )


def no_loss_model(
    *, mixture_type: propellants.MixtureType
) -> losses_base.NozzleLossModel:
    """An ideal model with no nozzle losses; the thrust coefficient is unchanged."""
    return losses_base.NozzleLossModel([], mixture_type=mixture_type)
