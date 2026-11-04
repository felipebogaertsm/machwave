# Testing

Applies to `tests/`.

## Layout

- `tests/` mirrors `machwave/`: `tests/test_core/` covers `machwave/core/`, and so on.
- Test objects come from the factories in `tests/factories/`; extend a factory instead of
  building objects by hand in each test.
- Performance benchmarks live in `tests/benchmarks/` and are skipped unless
  `make benchmark` runs them.
- `make test-core` runs a path-selected subset with no optional dependencies installed.
  A test that needs an extra must not be reachable from those paths.

## Markers

| Marker | Meaning |
| --- | --- |
| `core` | Exercises Machwave with only its core dependencies |
| `verification` | Compares against an analytical, manufactured or highly accurate reference, or measures order of accuracy |
| `validation` | Compares against measured data |

Unmarked tests are unit and regression tests.

## Tolerances

- Every tolerance has a stated reason: round-off (around 1e-12), the tolerance of an
  iterative solver, the discretization error measured by a convergence study, or the
  precision of the reference data. Reuse a named constant when the reason repeats.
- Pass the reference value as the expected value. Quantities that reach zero get an
  absolute tolerance.
- Assert against the source value of an expected number, not a decoded literal with a
  comment explaining it.
- Never loosen a tolerance or change an expected value to make a test pass without saying
  so in the pull request, with the reason.

## Convergence tests

- Use at least three refinement levels with a ratio of at least 1.3.
- Compute the observed order from successive error ratios and assert it against the
  formal order with a stated margin.
- Measure the order of the whole coupled time step, not only the inner solver.

## Writing tests

- Name a test after the behaviour it checks (`test_chamber_pressure_stays_positive_at_
  burnout`), never after the bug that was fixed.
- Every fixed bug gets a regression test.
- Test public behaviour. Do not call or patch private helpers; inject fakes that implement
  the real interface instead of patching external solvers.
- Use `pytest.raises(..., match=...)` and `pytest.warns(..., match=...)` with a message
  pattern.
- Seed any random input.
- Short comments are welcome where they say something the code cannot, such as why a
  parametrized case is invalid. No docstrings that restate the test name.
