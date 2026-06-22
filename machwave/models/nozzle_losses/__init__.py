"""Composable nozzle thrust coefficient loss models."""

from machwave.models.nozzle_losses import presets
from machwave.models.nozzle_losses.base import (
    NozzleLossEvaluationResult,
    NozzleLossModel,
    ThrustCoefficientTermTarget,
)

__all__ = [
    "NozzleLossEvaluationResult",
    "NozzleLossModel",
    "ThrustCoefficientTermTarget",
]
