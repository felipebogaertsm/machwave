# Testing patterns

How tests are written and run. Read this before editing `tests/` or adding tests for a
change.

## Suites

| Suite | Command | Needs | Covers |
| --- | --- | --- | --- |
| Full | `make test` | every extra (`make install-dev`) | the whole library |
| Core | `make test-core` | no extra (`make install-dev-core`) | what must work with only the core dependencies |
| Benchmarks | `make benchmark` | every extra | loop timings; skipped by `make test` |

- A test that must pass with no optional dependency sets `pytestmark = pytest.mark.core`
  and its path is added to the `test-core` target in the `Makefile`. The target selects
  by path, not by marker, because most of the suite cannot be imported without extras.
- Run the smallest test first: `uv run pytest tests/path/test_file.py::test_name`.

## Layout and helpers

- `tests/test_<package>` mirrors `machwave/<package>`.
- Build objects with the factories in `tests/factories`; each exposes
  `build(**overrides)`. Extend a factory instead of building objects by hand.
- Whole reference motors for simulation tests live in
  `tests/test_simulations/motor_builders.py`. Reuse them for before and after comparisons
  of a physics change.

## What a physical model is tested against

- An exact or independent reference: a closed-form case, a CAD geometry, a published
  table or worked example. Assert against the source value, with the source named.
- Discretized methods also assert their observed order of accuracy over at least three
  refinement levels, on every code path and grid parity.
- Invariants: conservation, non-negative masses and pressures, monotonic regression,
  surfaces that must not burn.
- Make a slow test faster by shrinking the problem, not by coarsening the discretization.

## Rules

- Every tolerance has a reason: round-off, solver tolerance, measured discretization
  error or reference precision. Never loosen one or change an expected value silently.
- Name tests after behaviour, not the fixed bug. Every fixed bug gets a test.
- Test public behaviour; do not patch private helpers. Match the message in
  `pytest.raises` and `pytest.warns`.
- Short comments are fine where the code cannot speak (why a case is invalid), never to
  explain a decoded literal; assert against the source value instead.
