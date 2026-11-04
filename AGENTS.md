# Machwave

Python library for rocket motor internal ballistics: solid rocket motors with fast
marching grain regression, and pressure-fed biliquid engines with chemical equilibrium
thermochemistry and real-fluid tanks.

## Commands

- `make install-dev`: install every extra and the development tools.
- `make format`, then `make check` (format, lint, type check) and `make test`.
- `make test-core`: tests that must pass with no optional dependencies.
- `make docs-deploy`: strict documentation build.
- One file: `uv run --all-extras pytest tests/test_core/test_mass_balance.py`.

The project uses uv; ignore a stale `VIRTUAL_ENV` in the shell. The `cea` extra needs
`gfortran` on macOS. Never edit `machwave/_version.py` (generated) or `uv.lock` by hand.

## Layout

Runtime imports run one way: `common` → `core` → `models` → `simulation` →
`montecarlo` and `adapters`. Upward imports only under `typing.TYPE_CHECKING`. The
solver wrappers in `services` (CEA, CoolProp) are imported lazily inside functions. The
core is internal ballistics: no trajectory or export helpers on `Motor`. Mass properties
stay generic (`machwave/common/mass_properties.py`), never coupled to an adapter.

## Before calling work done

- Run `make check` and `make test`; add `make docs-deploy` for documentation.
- Say which checks could not run and why. Never imply something was tested when it was
  not.
- For physics changes, state which verification case ran and its result.
- Docstrings, explanation pages and this file are updated in the same change that alters
  the pattern they describe.
- After about three failed attempts at the same failure, stop and report.

## Naming

- Names replace comments. Spell out meaning in domain terms: `chamber_pressure`,
  `isentropic_exponent`, `time_step`. Symbols go in the docstring, not the name.
- Do not abbreviate, including physics shorthand (`k`, `d_t`, `Isp`, `Kn`, `m_dot`).
  The only exceptions:
  - Python, NumPy and pytest names: `self`, `cls`, `args`, `kwargs`, `dtype`, fixtures.
  - The import aliases `np`, `npt` and `go`.
  - Tooling names: `env`, `venv`, `dev`, `docs`, `src`, `ci`, `os`, `sys`.
  - Proper names: CEA, CoolProp, NIST, JSON, CSV, URL, ID, API, `.eng`.
  - Unit symbols as suffixes (`pressure_psi`) and in conversion function names.
  - `rk4`, `ode`, `2d`, `3d`; `i`, `j` as short loop indices; `x`, `y`, `z` as
    coordinates; `min_` and `max_` prefixes.
- Functions are verbs, attributes nouns, booleans predicates (`is_choked`).
- One word per concept across solid and biliquid code, results, plots and docs.
- No empty words (`data`, `info`, `value`, `obj`) and no `utils` modules.
- Flags are keyword-only or enumerations. Constants are named, never bare numbers.

## Code

- Comments only for a reason the code cannot state. Never comment what the code does,
  and never mention issue or pull request numbers in source, docstrings or tests.
- Docstrings are short, with `Args`, `Returns` and `Raises` sections and SI units, wrapped
  at 88 characters (ruff does not check docstring line length).
- Namespace imports (`import machwave.core.conversions as conversions`); resolve a name
  clash with an alias, not a `from` import.
- SI everywhere. Every unit conversion calls `machwave/core/conversions.py`; keep its
  functions even when only tests use them.
- Optional dependencies go through `machwave/common/extras.py`.
- Raise specific exceptions whose message gives the quantity, its value and the allowed
  range. Warn with `stacklevel` set. New code never prints; reports return text.
- Smallest diff that solves the issue. Follow the nearest existing pattern. Reuse before
  adding; no thin wrappers; fix a shared function once instead of patching callers.
- A new dependency needs a reason and goes in an optional extra unless the core needs it.
- Renaming or removing public API goes through a deprecation warning first.

## Physical models

A new or changed model in `core` or `models` ships with:

- A `References:` docstring section: primary source, edition, equation or section.
- Assumptions, valid range and SI units in the docstring. Use outside the range warns or
  raises, never extrapolates silently.
- A test against an exact or independent reference solution. Discretized methods also
  assert their observed order of accuracy over at least three refinement levels.
- Tests of invariants: conservation, non-negative masses and pressures, monotonic
  regression.
- Its validation status: the measured data it matches, or "verified, not validated".
  Calibrated parameters say which data they were fitted to, and that data never
  validates the same model.

Never port code from GPL or commercially licensed software; implement from the paper.
Propellant and other bundled data state their source and units.

## Simulation

- `SolidMotorState` and `BiliquidEngineState` mirror each other: same `run_timestep`
  order, array conventions and names. Change both together unless the physics differs.
- Unread `TimestepConditions` fields are intentional; do not remove them.
- The coupled time step is first order: only chamber pressure goes through RK4.
- Fast marching `grid_resolution` never goes below 100. Speed up tests by shortening
  grains, not by coarsening the grid.
- Burn area changes are checked against a closed-form area or CAD, on both the 2D and 3D
  paths and on odd and even grids. Inhibited faces and casing walls never burn.
- The biliquid loop is bound by CEA evaluations; benchmark loop changes with
  `make benchmark`.

## Tests

- `tests/` mirrors `machwave/`; build objects with `tests/factories/`.
- Every tolerance has a reason (round-off, solver tolerance, measured discretization
  error, reference precision). Never loosen one or change an expected value silently.
- Name tests after behaviour, not the fixed bug. Every fixed bug gets a test.
- Test public behaviour; do not patch private helpers. Use `match=` with
  `pytest.raises` and `pytest.warns`.
- Short comments are fine where the code cannot speak (why a case is invalid). Assert
  against the source value, not a decoded literal explained by a comment.

## Documentation

Explanation pages in `docs/explanations/` are for readers who know propulsion: concept
and equations first, an `Implementation` section linking the classes last, then
`References` with editions. No code listings. Short, plain sentences: no rhetorical
openers, no "X, not Y" contrasts, no heavy bolding.

## Workflow

- Branch per issue: `{issue_number}-short-summary`. Independent bugs get separate issues,
  branches and pull requests.
- Commit subjects state the behaviour change; bodies explain the mechanism and the
  measured symptom. Stage files by explicit path.
- Pull request bodies are short and start with `Closes #<issue>.`
- Issues use standard propulsion terms ("biliquid", spell out a symbol on first use) and
  one or two sentences.
- No tool or assistant attribution in commits or pull requests.
