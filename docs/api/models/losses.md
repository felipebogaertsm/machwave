# models.losses

Composable nozzle thrust-coefficient loss models.

- `NozzleLossModel` — Composes an ordered list of `LossComponent` strategies, each derating the momentum term, the pressure term, or both of the decoupled thrust coefficient (`ThrustCoefficientTermTarget`). Owned by the `Motor`.
- `LossComponent` — One nozzle loss, a thin wrapper over a core loss formula in `core.compressible_flow.losses`, evaluated from a per-step `LossEvaluationContext`.
- Factory functions `spp1975_solid_loss_model`, `spp1975_biliquid_loss_model`, `constant_efficiency_loss_model`, and `no_loss_model` build configured models.

::: machwave.models.losses
