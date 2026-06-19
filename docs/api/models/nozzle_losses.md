# models.nozzle_losses

Composable nozzle thrust-coefficient loss models.

- `NozzleLossModel` — Composes an ordered list of `LossComponent` strategies, each derating the momentum term, the pressure term, or both of the decoupled thrust coefficient (`ThrustCoefficientTermTarget`). Owned by the `Motor`.
- `nozzle_losses.components` — The concrete losses: `DivergentLoss` (`divergent`), `ConstantFractionLoss` (`constant`), and the Solid Performance Program 1975 set `KineticsLoss`, `BoundaryLayerLoss`, `TwoPhaseFlowLoss` (`spp1975`), each evaluated from the simulation's per-step [`TimestepConditions`](../simulation.md).
- `nozzle_losses.presets` — Factory functions for ready-made models: `spp1975_solid_loss_model`, `constant_efficiency_loss_model`, `constant_plus_divergent_efficiency_loss_model`, and `no_loss_model`.

::: machwave.models.nozzle_losses
    options:
      members:
        - NozzleLossModel
        - NozzleLossEvaluationResult
        - ThrustCoefficientTermTarget

## Components

The empirical correlations (Solid Performance Program 1975, AFRPL-TR-75-36) live as `loss_fraction` static methods on the component classes below: pure functions of scalar inputs that are callable and testable on their own. Each component declares `timestep_parameter_sources`, a mapping from every `loss_fraction` parameter to the dotted attribute path it is read from on the per-step [`TimestepConditions`](../simulation.md); the inherited `get_loss_fraction` resolves those paths and feeds the correlation.

::: machwave.models.nozzle_losses.components

## Presets

::: machwave.models.nozzle_losses.presets
