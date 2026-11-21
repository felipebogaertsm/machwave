# Machwave

Open source Python library for chemical rocket propulsion simulation: solid motors and
biliquid engines, built on internal ballistics. Python 3 with uv. User documentation is
built with MkDocs from `docs/`.

## How to use these instructions

- Start here, then load only the docs mapped below to the paths you will touch.
- If the task grows into a new area, load that area's doc before editing there.
- The code is the source of truth. If a doc and the code disagree, trust the code and
  fix the doc. `docs/ai/README.md` says where a new rule goes.

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

## Layout

```
machwave/common/      shared types (fluid state, mass properties) and optional dependency loading
machwave/core/        physics primitives: compressible flow, mass balance, performance, unit conversions, solvers
machwave/models/      engine components: grain, propellants, nozzle losses, feed systems, thrust chamber, motors
machwave/simulation/  the time-marched loop and per-step state for solid and biliquid engines, and results
machwave/montecarlo/  dispersion studies over a simulation
machwave/adapters/    exporters to other libraries (RocketPy)
machwave/services/    thin wrappers over external solvers (CEA, CoolProp), .eng export and plots
tests/                test_<package> mirrors machwave/<package>; shared factories in tests/factories
```

Dependencies run one way: `common` → `core` → `models` → `simulation` → `montecarlo` and
`adapters`. A lower layer never imports a higher one at runtime. Adapters, exporters and
plots depend on the core and carry no physics of their own.

## Key commands

`make` is the single entry point; CI only sets up the environment and calls `make`
targets. A new routine command becomes a `make` target, never a step written only in a
workflow file.

- Install with every extra and the dev tools: `make install-dev`
- Format: `make format`
- Format check, lint and type check: `make check`
- Tests: `make test`. One file: `uv run pytest tests/test_core/test_performance.py`
- Tests with no optional dependency installed: `make install-dev-core`, then
  `make test-core`
- Coverage: `make coverage`. Benchmarks: `make benchmark`
- Documentation build as CI runs it: `make docs-deploy`

## Verification

- Do not claim work is complete without running verification.
- Run the smallest relevant test first, then `make check` and `make test`. Add
  `make docs-deploy` when `docs/`, `mkdocs.yml` or a docstring changed.
- For a physics change, state which verification test ran and its result.
- Say which checks could not run and why. Never imply something was tested when it was
  not.
- After about three failed attempts at the same failure, stop and report what you tried.

## Important caveats

- **SI everywhere.** Every unit conversion goes through a function in
  `machwave/core/conversions.py`, never an inline factor. Conversion functions stay
  even when only tests use them.
- **Optional dependencies load lazily** through `machwave.common.extras.require`, so the
  package imports and the core tests pass with no extra installed.
  `tests/test_optional_dependencies.py` enforces this.
- Generated files (`machwave/_version.py`) and `uv.lock` are never edited by hand.
- Public API is renamed or removed only through a deprecation warning first.
- Never port code from GPL or commercially licensed software; implement from the paper.
- Workflow:
  - Branch per issue: `{issue_number}-short-summary`. Independent bugs get separate
    issues, branches and pull requests.
  - Commit subjects state the behaviour change; bodies explain the mechanism and the
    measured symptom. Stage files by explicit path.
  - Pull request bodies are short and start with `Closes #<issue>.`
  - Issues use standard propulsion terms ("biliquid", spell out a symbol on first use)
    and one or two sentences.
  - No tool or assistant attribution in commits, pull requests or issues.
