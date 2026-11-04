# Physical models

Applies to `machwave/core/` and `machwave/models/`. A physical model is any function or
class that turns physical inputs into physical outputs through an equation, correlation or
numerical method.

## What every model ships with

A new or changed model is not done until each item holds. The pull request template asks
for them.

1. **Reference.** A `References:` docstring section with the primary source, its edition
   and the equation or section number. Prefer archival sources (books, journal papers,
   technical reports) over web pages.
2. **Assumptions and limits.** The docstring states the assumptions, the valid input
   range and the uses the model is meant for. A run outside the valid range warns or
   raises; it never returns a silent extrapolation.
3. **Units.** Every input and output documented in SI.
4. **Code verification.** A test against an analytical or manufactured solution. A
   discretized model (time step, `grid_resolution`, mesh) also asserts its observed order of
   accuracy over at least three refinement levels with a refinement ratio of at least 1.3.
5. **Independent reference comparison.** A test against a source the model did not come
   from: a CEA reference case, a NIST or CoolProp fluid state, a CAD-measured area or
   volume, a closed-form special case.
6. **Invariants.** Tests of the physical properties that must always hold over a range of
   inputs: mass conservation, non-negative masses and pressures, monotonic web regression,
   non-negative burn area.
7. **Validation status.** Either a comparison against measured data the model was not
   tuned on, or an explicit "verified, not validated" statement in the docstring and the
   explanation page.
8. **Calibration declared.** A parameter fitted to data (efficiencies, burn rate
   coefficients) is marked as calibrated, with the data it came from. That data is never
   used to validate the same model.

## References

- Pin the edition. A citation without an edition, or with an equation number from another
  edition, is incomplete.
- References support the docstring; the docstring must still be understandable without
  them.
- Do not put "based on" or "inspired by" comments in function bodies; the `References:`
  section is the only place for sources.

## Sources of code

- A model must be established in the literature.
- Never port code from GPL, CC-BY-SA or commercially licensed software. Implementing the
  method from the published paper or book is fine.

## Data files

Propellant cards and any other bundled data state their source, version or date, and the
units of every field.

## Scope of the core

- The core is internal ballistics. Methods that only trajectory or export consumers need do
  not go on `Motor`.
- Mass properties stay generic: `DryMassProperties` lives in
  `machwave/common/mass_properties.py`, is carried by the thrust chamber, and is never
  coupled to an adapter. Any consumer, not only adapters, must reach mass properties from a
  motor and a simulation result.

## Verification and validation vocabulary

Label every physics test by what it shows:

| Evidence | Question answered | Example |
| --- | --- | --- |
| Code verification | Are the equations solved correctly? | Observed order of the integrator against an exact solution |
| Solution verification | How large is the numerical error of this run? | Total impulse change between `grid_resolution` levels |
| Validation | Does the model match measured reality? | Chamber pressure against a static fire |

Code verification and validation are separate evidence; passing one never substitutes for
the other. Compare global quantities first (total impulse, burn time, average and peak
chamber pressure, specific impulse), then time histories.
