# Machwave

Machwave is an open source Python library for chemical rocket propulsion simulation.

## Commands

The `Makefile` is the single entry point for every command that matters: install, format,
check, test, docs, build and release. Continuous integration only sets up the
environment and calls `make` targets, so anything CI does can be run locally the same
way. A new routine command becomes a `make` target, never a step written only in a
workflow file.

The project uses uv. Generated files and the lock file are never edited by hand.

## Architecture

- Dependencies run one way: `common` → `core` → `models` → `simulation` →
  `montecarlo` and `adapters`. A lower layer never imports a higher one at runtime.
- The core of the library is internal ballistics. Exporters, plots and adapters to other
  libraries depend on the core, never the reverse, and carry no physics of their own.
- A quantity that more than one consumer may need (mass properties, results) is owned by
  the core or a shared type, never by one consumer.
- External solvers sit behind thin service wrappers and are imported lazily, so the
  package imports and the core tests pass with no optional dependency installed.
- Implementations of one abstraction keep the same structure: every `MotorState` has the
  same step order, array conventions and names, every grain geometry exposes the same
  quantities. A change to one is mirrored in the others unless the physics differs.
- Extension seams are deliberate: a per-step snapshot may carry fields that no current
  consumer reads. Do not remove them as dead code.

## Designing a change

- Solve the issue with the smallest change that fits the existing design. Follow the
  nearest existing pattern; reuse before adding; the standard library before a
  dependency; a dependency before new code.
- Fix a shared function once instead of patching its callers.
- No thin wrappers, no speculative parameters, no `utils` modules.
- A new dependency needs a reason and goes in an optional extra unless the core needs it.
- Public API is renamed or removed only through a deprecation warning first.
- Correct first, then clear, then fast. Optimize only with a measurement; loop cost is
  dominated by external solver evaluations, so count them.
- Docstrings, explanation pages and this file change in the same change that alters the
  pattern they describe. A doc that teaches the old pattern is a defect.

## Before calling work done

- Run `make check` and `make test`; add `make docs-deploy` for documentation.
- Say which checks could not run and why. Never imply something was tested when it was
  not.
- For physics changes, state which verification case ran and its result.
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
- One word per concept across every motor type, results, plots and docs.
- No empty words (`data`, `info`, `value`, `obj`).
- Flags are keyword-only or enumerations. Constants are named, never bare numbers.

## Code

- Comments only for a reason the code cannot state. Never comment what the code does,
  and never mention issue or pull request numbers in source, docstrings or tests.
- Docstrings are short, with `Args`, `Returns` and `Raises` sections and SI units, and
  follow the code line length.
- Namespace imports; resolve a name clash with an alias, not a `from` import.
- SI everywhere. Every unit conversion goes through a conversion function, never an
  inline factor. Conversion functions stay even when only tests use them.
- Raise specific exceptions whose message gives the quantity, its value and the allowed
  range. Warn with `stacklevel` set. New code never prints; reports return text.

## Physical models

A new or changed model ships with:

- A `References:` docstring section: primary source, edition, equation or section.
- Assumptions, valid range and SI units in the docstring. Use outside the range warns or
  raises, never extrapolates silently.
- A test against an exact or independent reference solution: closed-form cases, CAD
  geometry, published tables. Discretized methods also assert their observed order of
  accuracy over at least three refinement levels, on every code path and grid parity.
- Tests of invariants: conservation, non-negative masses and pressures, monotonic
  regression, surfaces that must not burn.
- Its validation status: the measured data it matches, or "verified, not validated".
  Calibrated parameters say which data they were fitted to, and that data never
  validates the same model.
- The order of accuracy stated for a coupled scheme is the global order, not the order
  of its inner solver.

Resolution floors and default time steps come from convergence studies; never lower one
for speed. Make a test faster by shrinking the problem, not by coarsening the
discretization.

Never port code from GPL or commercially licensed software; implement from the paper.
Propellant and other bundled data state their source and units.

## Tests

- `tests/` mirrors `machwave/`; build objects with the shared test factories.
- Every tolerance has a reason (round-off, solver tolerance, measured discretization
  error, reference precision). Never loosen one or change an expected value silently.
- Name tests after behaviour, not the fixed bug. Every fixed bug gets a test.
- Test public behaviour; do not patch private helpers. Match the message in
  `pytest.raises` and `pytest.warns`.
- Short comments are fine where the code cannot speak (why a case is invalid). Assert
  against the source value, not a decoded literal explained by a comment.

## Documentation

Explanation pages are for readers who know propulsion: concept and equations first, an
`Implementation` section linking the classes last, then `References` with editions. No
code listings. Short, plain sentences: no rhetorical openers, no "X, not Y" contrasts,
no heavy bolding.

## Workflow

- Branch per issue: `{issue_number}-short-summary`. Independent bugs get separate issues,
  branches and pull requests.
- Commit subjects state the behaviour change; bodies explain the mechanism and the
  measured symptom. Stage files by explicit path.
- Pull request bodies are short and start with `Closes #<issue>.`
- Issues use standard propulsion terms ("biliquid", spell out a symbol on first use) and
  one or two sentences.
- No tool or assistant attribution in commits or pull requests.
