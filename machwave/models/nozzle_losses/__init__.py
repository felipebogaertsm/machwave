"""Composable nozzle thrust coefficient loss models."""

__all__ = [
    "NozzleLossEvaluationResult",
    "NozzleLossModel",
    "ThrustCoefficientTermTarget",
]

from machwave.models.nozzle_losses import presets
from machwave.models.nozzle_losses.base import (
    NozzleLossEvaluationResult,
    NozzleLossModel,
    ThrustCoefficientTermTarget,
)
