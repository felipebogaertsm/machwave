import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components as losses_components
import machwave.models.propellants as propellants

_SOLID = propellants.MixtureType.SOLID
_BILIQUID = propellants.MixtureType.BILIQUID

DEFAULT_OTHER_LOSSES = 0.05


def spp1975_solid_loss_model(
    *, other_losses: float = DEFAULT_OTHER_LOSSES
) -> losses_base.NozzleLossModel:
    """Solid Performance Program 1975 nozzle loss set for a solid motor."""
    return losses_base.NozzleLossModel(
        [
            losses_components.DivergenceLoss(),
            losses_components.KineticsLoss(),
            losses_components.BoundaryLayerLoss(),
            losses_components.TwoPhaseFlowLoss(),
            losses_components.ConstantFractionLoss(other_losses, name="other_losses"),
        ],
        mixture_type=_SOLID,
    )


def spp1975_biliquid_loss_model(
    *, other_losses: float = DEFAULT_OTHER_LOSSES
) -> losses_base.NozzleLossModel:
    """Solid Performance Program 1975 nozzle loss subset for a biliquid engine."""
    return losses_base.NozzleLossModel(
        [
            losses_components.DivergenceLoss(),
            losses_components.KineticsLoss(),
            losses_components.ConstantFractionLoss(other_losses, name="other_losses"),
        ],
        mixture_type=_BILIQUID,
    )


def constant_efficiency_loss_model(
    efficiency: float, *, mixture_type: propellants.MixtureType
) -> losses_base.NozzleLossModel:
    """A flat nozzle efficiency applied to the whole thrust coefficient."""
    return losses_base.NozzleLossModel(
        [
            losses_components.ConstantFractionLoss(
                1.0 - efficiency, name="constant_efficiency_loss"
            )
        ],
        mixture_type=mixture_type,
    )


def no_loss_model(
    *, mixture_type: propellants.MixtureType
) -> losses_base.NozzleLossModel:
    """An ideal model with no nozzle losses; the thrust coefficient is unchanged."""
    return losses_base.NozzleLossModel([], mixture_type=mixture_type)
