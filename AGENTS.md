# Machwave

Open source Python library for chemical rocket propulsion simulation: solid motors and
biliquid engines, built on internal ballistics.

## How to use these instructions

- Start here, then load only the docs mapped below to the paths you will touch.
- If the task grows into a new area, load that area's doc before editing there.
- The code is the source of truth. If a doc and the code disagree, trust the code and
  fix the doc.

## Before you edit

- **Any Python in `machwave/` or `tests/`:** read `docs/ai/code-style.md`.
- **A physical model in `machwave/core` or `machwave/models`** (losses, propellants,
  grain geometries, feed systems, thrust chamber): read `docs/ai/physical-models.md`.
- **`machwave/simulation`, `machwave/core/solvers` or `machwave/models/grain/fmm`:** read
  `docs/ai/simulation-patterns.md`.
- **`tests/`, or adding tests for a change:** read `docs/ai/testing-patterns.md`.
- **`docs/`, `mkdocs.yml`, or a change to public API or behaviour:** read
  `docs/ai/documentation.md`.
- **This file or anything in `docs/ai/`:** read `docs/ai/README.md`.

## Key commands

`make` is the single entry point; CI only sets up the environment and calls `make`
targets. A new routine command becomes a `make` target, never a step written only in a
workflow file.

- Install with every extra and the dev tools: `make install-dev`
- Format: `make format`
- Format check, lint and type check: `make check`
- Tests: `make test`. One file: `uv run pytest tests/test_core/test_performance.py`
- Documentation build as CI runs it: `make docs-deploy`

## Verification

- Run the smallest relevant test first, then `make check` and `make test`. Add
  `make docs-deploy` when `docs/`, `mkdocs.yml` or a docstring changed.
- For a physics change, state which verification test ran and its result.
- Say which checks could not run and why. Never imply something was tested when it was
  not.
- After about three failed attempts at the same failure, stop and report what you tried.

## Important caveats

- **Dependencies run one way:** `common` → `core` → `models` → `simulation` →
  `montecarlo` and `adapters`. A lower layer never imports a higher one at runtime.
  Adapters, exporters and plots carry no physics of their own.
- **SI everywhere.** Every unit conversion goes through a function in
  `machwave/core/conversions.py`, never an inline factor. Conversion functions stay
  even when only tests use them.
- **Optional dependencies** are imported through `machwave.common.extras.require`, at
  the point of use, so the package imports with no extra installed.
  `tests/test_optional_dependencies.py` fails otherwise.
- `machwave/_version.py` and `uv.lock` are generated. Never edit them by hand.
- Public API is renamed or removed only after a deprecation warning.
- Never port code from GPL or commercially licensed software; implement from the paper.
- Workflow:
  - Branch per issue: `{issue_number}-short-summary`. Independent bugs get separate
    issues, branches and pull requests.
  - Commit subjects state the behaviour change; bodies explain the mechanism and the
    measured symptom. Stage files by explicit path.
  - Issues and pull requests follow the forms in `.github/ISSUE_TEMPLATE/` and
    `.github/PULL_REQUEST_TEMPLATE.md`, in plain language and standard propulsion terms
    ("biliquid", spell out a symbol on first use). Leave out the optional sections
    that do not apply.
  - No tool or assistant attribution in commits, pull requests or issues.
