# Physical models

How a model in `machwave/core` or `machwave/models` is written: loss components,
propellants, grain geometries, feed system components and any other equation.

## What a model ships with

- A `References:` docstring section: primary source, edition, equation or section.
- Assumptions, valid range and SI units in the docstring. Use outside the range warns or
  raises, never extrapolates silently.
- Tests as described in `docs/ai/testing-patterns.md`.
- Its validation status: the measured data it matches, or "verified, not validated".
  Calibrated parameters say which data they were fitted to, and that data never
  validates the same model.
- Bundled data (propellant formulations) states its source and units.

Most existing models have no `References:` section or range check, and the JSON
formulations in `machwave/models/propellants/formulations` state no source.

## Calibration envelopes

- An empirical correlation is valid only for the propellants and conditions of the data
  it was fitted to. The SPP 1975 loss correlations
  (`machwave/models/nozzle_losses/components/spp1975.py`) are fitted to aluminized
  composite propellants; sugar propellants (KNDX, KNSB) are outside their envelope.
- `applicable_mixture_types` only separates solid from biliquid. A correlation tied to a
  propellant family also checks the propellant itself.

## Losses

- Combustion efficiency acts on the characteristic velocity, through the flame
  temperature (`machwave/core/performance.py`). Nozzle losses act on the thrust
  coefficient, per term. Never count one effect on both sides.
