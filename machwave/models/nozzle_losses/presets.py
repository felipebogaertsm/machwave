import machwave.models.nozzle_losses.base as losses_base
import machwave.models.nozzle_losses.components.constant as constant
import machwave.models.nozzle_losses.components.divergent as divergent
import machwave.models.nozzle_losses.components.spp1975 as spp1975
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
            divergent.DivergentLoss(),
            spp1975.KineticsLoss(),
            spp1975.BoundaryLayerLoss(),
            spp1975.TwoPhaseFlowLoss(),
            constant.ConstantFractionLoss(other_losses, name="other_losses"),
        ],
        mixture_type=_SOLID,
    )


def constant_efficiency_loss_model(
    efficiency: float = DEFAULT_NOZZLE_EFFICIENCY,
    *,
    mixture_type: propellants.MixtureType,
) -> losses_base.NozzleLossModel:
    """A flat efficiency plus the geometric nozzle divergence loss."""
    return losses_base.NozzleLossModel(
        [
            constant.ConstantFractionLoss(
                1.0 - efficiency, name=_CONSTANT_EFFICIENCY_LOSS_NAME
            ),
            divergent.DivergentLoss(),
        ],
        mixture_type=mixture_type,
    )


def no_loss_model(
    *, mixture_type: propellants.MixtureType
) -> losses_base.NozzleLossModel:
    """An ideal model with no nozzle losses; the thrust coefficient is unchanged."""
    return losses_base.NozzleLossModel([], mixture_type=mixture_type)
