# models.nozzle_losses

Composable nozzle thrust-coefficient loss models.

- `NozzleLossModel` — Composes an ordered list of `LossComponent` strategies, each derating the momentum term, the pressure term, or both of the decoupled thrust coefficient (`ThrustCoefficientTermTarget`). Owned by the `Motor`.
- `LossComponent` — One nozzle loss, evaluated from a per-step `LossEvaluationContext`. Concrete components live in `components/`: `DivergenceLoss` (`divergent`), `ConstantFractionLoss` (`constant`), and the Solid Performance Program 1975 set `KineticsLoss`, `BoundaryLayerLoss`, `TwoPhaseFlowLoss` (`spp1975`).
- Preset models are built by the factory functions in `nozzle_losses.presets`: `spp1975_solid_loss_model`, `spp1975_biliquid_loss_model`, `constant_efficiency_loss_model`, and `no_loss_model`.

::: machwave.models.nozzle_losses

## Loss correlations

The empirical correlations backing the components (Solid Performance Program 1975, AFRPL-TR-75-36), kept as pure functions.

::: machwave.models.nozzle_losses.components.divergent
    options:
      members:
        - get_nozzle_divergent_loss_fraction

::: machwave.models.nozzle_losses.components.spp1975
    options:
      members:
        - get_kinetics_loss_fraction
        - get_boundary_layer_loss_fraction
        - get_two_phase_flow_loss_fraction

## Presets

::: machwave.models.nozzle_losses.presets
