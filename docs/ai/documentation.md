# Documentation

Applies to `docs/`, `examples/` and `scripts/`.

## Kinds of pages

| Kind | Where | Purpose |
| --- | --- | --- |
| Tutorial | `docs/quickstart.md` | Takes a new user from install to a first simulation |
| Explanation | `docs/explanations/` | Physics and modelling choices |
| Reference | `docs/api/` | Generated from docstrings by mkdocstrings |
| Examples | `examples/` | Runnable scripts for real motors and engines |

A new page goes in `mkdocs.yml` navigation. `make docs-deploy` builds in strict mode and
must pass. `docs/ai/` and the agent instruction files are excluded from the published
site.

## Explanation pages

- Written for readers who know rocket propulsion and college mathematics and physics. Use
  standard terms without defining basics.
- Concept first: what happens and why, in equations and tables. No class or method names,
  code listings, array conventions or validation ranges in the body.
- Close with an `Implementation` section: which Machwave objects own which part, how they
  compose, with cross-reference links to the API pages. Still no code listings; lookup
  material stays in `docs/api/`.
- End with a `References` section, citing editions and equation numbers.
- Short sentences, facts in tables and equations, at most one example per idea.
- Avoid prose that reads as generated: no rhetorical openers, no "X, not Y" contrasts, no
  "the natural fix" or "the price is", no heavy bolding.

## Figures

- Figures come from real example motors and real simulation output, never invented curves.
- Animations are looping SVG files animated with SMIL and embedded as images, not GIFs.
  All animated elements share one timeline; frames change with hard cuts, no fades.
- Keep the plot as the main element, with few and short step labels. Orange `#e2683c`
  marks the current instant.
- Verify an animation by freezing it at chosen instants in a headless browser
  (`svg.pauseAnimations(); svg.setCurrentTime(t)`) and looking at the frames before
  publishing.
- A figure generator is a script in `scripts/` that runs the real models, so the figure
  can be regenerated when the models change.

## Examples

- An example must run with `uv run --all-extras python examples/<name>.py`.
- Examples use public API only and the same naming rules as the package.
