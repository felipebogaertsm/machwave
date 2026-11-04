---
name: machwave-review
description: Review the current branch of Machwave against its engineering standard (naming, abbreviations, layering, physical model evidence, tolerances, references, docs). Use when asked to review a branch, a diff or a pull request in this repository.
---

# Review a Machwave change

Read-only. Do not edit files, install tools or run anything beyond the commands below.

## Gather the change

1. `git diff --stat origin/master...HEAD`, then the diff of each changed file except
   `uv.lock`, generated files and binaries.
2. Read `AGENTS.md` and the guides in `docs/ai/` mapped to the changed paths.
3. For each changed module, open one or two sibling modules to compare patterns and spot
   duplication.

Comment only on changed lines and on what the change makes inconsistent elsewhere.

## Check, in this order

1. **Correctness and physics.** Equations match their cited source and edition; units are
   SI and consistent; signs, limits and edge cases (zero mass, burnout, choked to unchoked
   flow) hold; no silent extrapolation outside a model's valid range.
2. **Evidence.** A changed physical model has every item of the model checklist in
   `docs/ai/physical-models.md`: reference, assumptions and limits, units, code
   verification, independent reference comparison, invariants, validation status,
   declared calibration.
3. **Tests.** Every tolerance has a reason; no tolerance loosened or expected value
   changed without explanation; regression tests named after behaviour; no patched private
   helpers.
4. **Layering.** Runtime imports follow `common` → `core` → `models` → `simulation` →
   `montecarlo` and `adapters`; upward imports only under `typing.TYPE_CHECKING`; no
   trajectory or export helpers on `Motor`.
5. **Duplication and simplicity.** Reuse over new code; no thin wrappers; no speculative
   parameters; the shared function fixed once.
6. **Naming.** Every new identifier is spelled out, with abbreviations only from the
   exception list in `docs/ai/code-style.md`; one word per concept across solid and
   biliquid code; verbs for functions, nouns for attributes, predicates for booleans.
7. **Comments and docstrings.** No comment a better name could replace; no issue numbers;
   short docstrings in the configured section style, wrapped at 88 characters, with
   `References:` on physical models.
8. **Units and conversions.** No inline unit factors; conversions through
   `machwave/core/conversions.py`.
9. **Documentation.** Guides, docstrings and explanation pages that describe a changed
   pattern are updated in the same change.

## Output

- **Summary:** two or three sentences on what the change does and whether it is ready.
- **Blockers:** only real risks to correctness or the standard.
- **Comments:** one per finding, with `path:line`, the problem in plain words, and a
  `Why:` line naming the concrete consequence.
- **Intentional choices (do not change):** patterns that look odd but are deliberate, such
  as unread `TimestepConditions` fields or kept conversion functions.
- **Follow-ups:** work that belongs in a separate issue.

If there is nothing to raise, say "No comments; ready to merge."
