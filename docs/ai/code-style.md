# Code style

Python conventions for `machwave/` and `tests/` that `make check` (ruff and pyright)
does not enforce.

## Designing a change

- Solve the issue with the smallest change that fits the existing design, following the
  nearest existing pattern.
- Reuse before adding: an existing function before a new one, the standard library
  before a dependency, a dependency before new code. A new dependency goes in an optional
  extra unless the core needs it.
- No thin wrappers, no speculative parameters, no `utils` modules.
- A quantity that more than one consumer needs (mass properties, results) is owned by the
  core or a shared type, never by one consumer.

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
- Older code still uses abbreviations such as `d_t` and `k_chamber`. Do not copy them
  into new code.
- Functions are verbs, attributes nouns, booleans predicates (`is_choked`).
- One word per concept across every motor type, results, plots and docs.
- No empty words (`data`, `info`, `value`, `obj`).
- Flags are keyword-only or enumerations. Constants are named, never bare numbers.

## Code

- Namespace imports (`import machwave.models.propellants as propellants`); resolve a name
  clash with an alias, not a `from` import.
- Docstrings are short, with `Args`, `Returns` and `Raises` sections and SI units in
  brackets.
- Comments only for a reason the code cannot state. Never mention issue or pull request
  numbers in source, docstrings or tests.
- Raise specific exceptions whose message gives the quantity, its value and the allowed
  range. Warn with `stacklevel` set. New code never prints; reports return text.

## Module layout

1. Module docstring.
2. `from __future__` imports.
3. Module dunders such as `__all__`.
4. Imports, grouped standard library, third party, local. Ruff checks this part.
5. Module constants and globals.
6. Functions and classes.

- Constants go right after the imports, never between functions. The only exception is
  a constant built from a function or class defined in the same module, such as
  `_GENERATOR_REGISTRY` in `machwave/montecarlo/random.py`.
- An import that needs a name its package is still binding goes after an
  `# isort: split` comment that says why, as in `machwave/models/grain/__init__.py`.
