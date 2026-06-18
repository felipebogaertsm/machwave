"""Composable nozzle thrust-coefficient loss models."""

from machwave.models.losses.base import (
    LossComponent,
    LossEvaluationContext,
    NozzleLossModel,
    NozzleLossResult,
    ThrustCoefficientTermTarget,
)
from machwave.models.losses.components import (
    BoundaryLayerLoss,
    ConstantFractionLoss,
    DivergenceLoss,
    KineticsLoss,
    TwoPhaseFlowLoss,
)
from machwave.models.losses.models import (
    DEFAULT_OTHER_LOSSES,
    constant_efficiency_loss_model,
    no_loss_model,
    spp1975_biliquid_loss_model,
    spp1975_solid_loss_model,
)

__all__ = [
    "LossComponent",
    "LossEvaluationContext",
    "NozzleLossModel",
    "NozzleLossResult",
    "ThrustCoefficientTermTarget",
    "BoundaryLayerLoss",
    "ConstantFractionLoss",
    "DivergenceLoss",
    "KineticsLoss",
    "TwoPhaseFlowLoss",
    "DEFAULT_OTHER_LOSSES",
    "constant_efficiency_loss_model",
    "no_loss_model",
    "spp1975_biliquid_loss_model",
    "spp1975_solid_loss_model",
]
