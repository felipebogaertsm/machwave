# Machwave

Machwave is a Python library for rocket motor internal ballistics: solid rocket motors
with fast marching grain regression in two and three dimensions, and pressure-fed
biliquid engines with chemical equilibrium thermochemistry and real-fluid tanks. Every
change must hold a high standard of code, architecture, physical verification and
references.

## How to use these instructions

- Read this file, then only the guides mapped below to the paths you will touch. Load
  more guides when the scope grows; do not preload all of them.
- The code is the source of truth. A guide that teaches an outdated pattern is a defect:
  update it in the same change that breaks the pattern.
- Guides describe patterns, not inventories. Adding a grain geometry or a propellant card
  should not need a guide change; changing how geometries or cards work should.
- Subdirectories with their own `AGENTS.md` add rules for that subtree.

## Before you edit

| Work in | Read first |
| --- | --- |
| Any Python file | [docs/ai/code-style.md](docs/ai/code-style.md) |
| `machwave/core/**`, `machwave/models/**` | [docs/ai/physical-models.md](docs/ai/physical-models.md) |
| `machwave/models/grain/**` | [docs/ai/grain-regression.md](docs/ai/grain-regression.md) |
| `machwave/simulation/**` | [docs/ai/simulation.md](docs/ai/simulation.md) |
| `tests/**` | [docs/ai/testing.md](docs/ai/testing.md) |
| `docs/**`, `scripts/**`, `examples/**` | [docs/ai/documentation.md](docs/ai/documentation.md) |
| Branches, commits, issues, pull requests | [docs/ai/workflow.md](docs/ai/workflow.md) |

Playbooks for recurring work live in `.claude/skills/`: `machwave-review` for reviewing a
branch and `add-physical-model` for adding or changing a physical model. Any agent can
read them as plain Markdown.

## Package layout

| Package | Holds |
| --- | --- |
| `machwave/common` | Shared types with no physics: optional dependency handling, fluid state, mass properties |
| `machwave/core` | Physics functions: compressible flow, mass balance, performance, solvers, unit conversions |
| `machwave/models` | Physical components: grains, propellants, nozzle losses, feed systems, thrust chambers, motors |
| `machwave/simulation` | Time marching states, simulations and results |
| `machwave/montecarlo` | Dispersion studies over simulations |
| `machwave/services` | Wrappers around external solvers (`cea.py`, `coolprop.py`) and output formats (`.eng`, plots) |
| `machwave/adapters` | Conversion of Machwave objects into other libraries' objects |

Runtime imports run one way: `common` → `core` → `models` → `simulation` →
`montecarlo` and `adapters`. A lower layer may import a higher one only under
`typing.TYPE_CHECKING`. The external solver wrappers in `services` are imported lazily,
inside the function that needs them. The core of the library is internal ballistics;
exporters and adapters depend on it, never the reverse.

## Commands

| Command | What it does |
| --- | --- |
| `make install-dev` | Install every extra and the development tools |
| `make format` | Format and autofix |
| `make check` | Format check, lint, type check |
| `make test` | Full test suite in parallel |
| `make test-core` | Tests that must pass with no optional dependencies installed |
| `make coverage` | Branch coverage report |
| `make benchmark` | Performance benchmarks |
| `make docs-deploy` | Strict documentation build, as continuous integration runs it |

Run a single file first: `uv run --all-extras pytest tests/test_core/test_mass_balance.py`.

## Verification

- Do not call work done without running `make check` and `make test`. For documentation
  changes, also run `make docs-deploy`.
- Start with the smallest relevant check, then run the full gates.
- The gates are green on `master`, so a failing check comes from the change.
- If a check could not run (missing extra, Fortran compiler, network), say which one and
  why. Never imply something was tested when it was not.
- After about three failed attempts at the same failure, stop and report what you found.
- For a physics change, state which verification or validation case was run and its
  result, not only that the tests pass.
- Before finishing, reread the guides you loaded and confirm their patterns still hold.

## Rules that apply everywhere

- Names replace comments. Do not abbreviate outside the closed exception list in
  [docs/ai/code-style.md](docs/ai/code-style.md).
- SI units inside the package. Every unit conversion calls a function in
  `machwave/core/conversions.py`; add one there if it is missing.
- Every physical model cites its primary source with edition and equation or section.
- Never mention issue or pull request numbers in source files, docstrings or tests.
- Keep namespace imports (`import machwave.core.conversions as conversions`); resolve a
  name clash with an alias, not a `from` import.
- The smallest diff that solves the issue. Fix a shared function once instead of patching
  its callers.

## Important caveats

- The project uses uv. A shell may export a stale `VIRTUAL_ENV` from an old environment;
  ignore it and use `uv run`.
- The `cea` extra builds a Fortran extension: macOS needs `gfortran` (see `README.md`).
- `machwave/_version.py` is generated from git tags. Never edit it; never hand-edit
  `uv.lock` either (use `uv add` or `uv lock`).
- Several agent sessions may share this working tree through worktrees. Stage files by
  explicit path, never with `git add -A`.
- Fast marching grain `grid_resolution` has a floor of 100. Do not lower it to speed up
  tests; see [docs/ai/grain-regression.md](docs/ai/grain-regression.md).
