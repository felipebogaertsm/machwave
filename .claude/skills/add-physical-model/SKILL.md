---
name: add-physical-model
description: Add or change a physical model in Machwave (an equation, correlation, loss component, propellant behaviour, feed component or numerical method) together with its references, limits and verification tests. Use when implementing new physics in machwave/core or machwave/models.
---

# Add or change a physical model

## 1. Pin the source

- Identify the primary source: book with edition, journal paper or technical report, and
  the exact equation or section numbers.
- If the method only exists in GPL, CC-BY-SA or commercial code, implement it from the
  publication, never from that code.
- List the assumptions, the valid input range and the intended uses from the source.

## 2. Place it

- Stateless equation: a function in the matching `machwave/core/` module.
- Component with parameters: a class in the matching `machwave/models/` package, following
  its nearest sibling.
- Read `docs/ai/physical-models.md` and `docs/ai/code-style.md` first.

## 3. Write it

- Spelled-out names; symbols only in the docstring, mapped to the source's notation.
- SI inputs and outputs; conversions through `machwave/core/conversions.py`.
- Docstring: one-line summary, `Args` and `Returns` with units, `Raises`, and
  `References:` with edition and equation numbers.
- Inputs outside the valid range raise the specific Machwave exception, or warn when the
  result is still usable.
- Constants are named, with their source.

## 4. Verify it

Add tests under the mirrored path in `tests/`:

- `verification`: an analytical or closed-form special case. For a discretized method,
  assert the observed order over at least three refinement levels with a ratio of at
  least 1.3.
- An independent reference comparison: a published table, CEA, NIST, CoolProp or CAD.
- Invariants over a range of inputs: conservation, non-negativity, monotonicity.
- Each tolerance with its reason.

## 5. Document it

- Declare the validation status in the docstring: the measured data it was compared
  against, or "verified, not validated".
- Mark calibrated parameters and their source data.
- Update the explanation page that covers the physics, with the reference in its
  `References` section, and add the model to `docs/api/`.

## 6. Finish

Run `make check`, `make test` and, if docs changed, `make docs-deploy`. In the pull
request, fill in the physical model checklist and state which verification cases ran and
their results.
