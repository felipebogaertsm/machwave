# machwave/core

Physics functions with no state: compressible flow, mass balance, performance, solvers and
unit conversions. Read [docs/ai/physical-models.md](../../docs/ai/physical-models.md)
before editing.

- Functions here take and return SI floats or NumPy arrays; no Machwave model objects.
- Imports go only to `machwave.common`, the standard library and the core dependencies
  in `pyproject.toml`. External solver wrappers in `machwave.services` are imported
  lazily or under `typing.TYPE_CHECKING`.
- Every equation function cites its source in a `References:` section.
- `conversions.py` is the only place for unit factors. Keep every conversion function,
  even when only tests call it.
