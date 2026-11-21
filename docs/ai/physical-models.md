# Physical models

How a model in `machwave/core` or `machwave/models` is written. Read this before adding
or changing a loss component, propellant, grain geometry, feed system component or any
other equation.

## What a model ships with

- A `References:` docstring section: primary source, edition, equation or section.
  Implement from the primary source, not from another code.
- Assumptions, valid range and SI units in the docstring. Use outside the range warns or
  raises, never extrapolates silently.
- Tests against an exact or independent reference and of its invariants, as described in
  `docs/ai/testing-patterns.md`.
- Its validation status: the measured data it matches, or "verified, not validated".
  Calibrated parameters say which data they were fitted to, and that data never
  validates the same model.

Most existing models do not have a `References:` section or a range check yet. Add them
to every model you write or change; leave the others alone.

## Calibration envelopes

- An empirical correlation is valid only for the propellants and conditions of the data
  it was fitted to. The SPP 1975 loss correlations are fitted to aluminized composite
  propellants; applying them to sugar propellants (KNDX, KNSB) or other condensed
  products is outside their envelope.
- Loss components declare the engine types they apply to in `applicable_mixture_types`,
  and `NozzleLossModel` rejects the rest. That is the coarse guard; a correlation tied to
  one propellant family also needs a check on the propellant itself.

## Thrust coefficient and losses

- The ideal thrust coefficient is kept as a momentum term and a pressure term. Each loss
  component declares which one it derates in `target`: divergence derates only the
  momentum term (`machwave/models/nozzle_losses/components/divergent.py`).
- Losses that act on the characteristic velocity (combustion efficiency) and losses that
  act on the thrust coefficient (nozzle losses) are applied in separate places. Never
  count one effect on both sides.

## Same structure across implementations

- Implementations of one abstraction keep the same structure: every grain geometry
  exposes the same quantities through `machwave/models/grain/base.py`. A change to one
  is mirrored in the others unless the physics differs.
- Grain geometry is an implementation choice: BATES is computed in closed form, the
  others with the fast marching method. Do not call a geometry "analytical".

## Data

- Propellant formulations and other bundled data state their source and units. The
  JSON formulations in `machwave/models/propellants/formulations` do not yet; a new or
  edited one does.
