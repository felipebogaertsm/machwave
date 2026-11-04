# tests

Read [docs/ai/testing.md](../docs/ai/testing.md) before editing.

- Mirror the package layout and build objects through `tests/factories/`.
- Every tolerance has a stated reason; never loosen one silently.
- Mark comparisons against exact or reference solutions `verification` and comparisons
  against measured data `validation`.
- Run a single file first: `uv run --all-extras pytest <path>`, then `make test`.
