# machwave/models

Physical components: grains, propellants, nozzle losses, feed systems, thrust chambers and
motors. Read [docs/ai/physical-models.md](../../docs/ai/physical-models.md) before
editing; for grains also read
[docs/ai/grain-regression.md](../../docs/ai/grain-regression.md).

- Models hold parameters and compute from them; time marching belongs in
  `machwave.simulation`. Imports of `machwave.simulation` stay under
  `typing.TYPE_CHECKING`.
- Validate inputs where the model is built and raise the specific Machwave exception with
  the quantity, its value and the allowed range.
- Propellant cards state their source and units.
- Do not add trajectory or export helpers to `Motor`.
