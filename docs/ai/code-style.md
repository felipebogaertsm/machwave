# Code style

Python conventions for `machwave/` and `tests/`. Formatting, lint and types are enforced
by `make check` (ruff and pyright); this file covers what those tools do not.

## Designing a change

- Solve the issue with the smallest change that fits the existing design. Follow the
  nearest existing pattern; reuse before adding; the standard library before a
  dependency; a dependency before new code.
- Fix a shared function once instead of patching its callers.
- No thin wrappers, no speculative parameters, no `utils` modules.
- A new dependency needs a reason and goes in an optional extra unless the core needs it.
- A quantity that more than one consumer needs (mass properties, results) is owned by the
  core or a shared type, never by one consumer.
- Correct first, then clear, then fast. Optimize only with a measurement.

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
- Older code still has abbreviations such as `d_t`. Do not copy them into new code.
- Functions are verbs, attributes nouns, booleans predicates (`is_choked`).
- One word per concept across every motor type, results, plots and docs.
- No empty words (`data`, `info`, `value`, `obj`).
- Flags are keyword-only or enumerations. Constants are named, never bare numbers.

## Code

- Namespace imports (`import machwave.models.propellants as propellants`); resolve a name
  clash with an alias, not a `from` import.
- Docstrings are short, with `Args`, `Returns` and `Raises` sections and SI units in
  brackets, and follow the code line length.
- Comments only for a reason the code cannot state. Never comment what the code does,
  and never mention issue or pull request numbers in source, docstrings or tests.
- Raise specific exceptions whose message gives the quantity, its value and the allowed
  range. Warn with `stacklevel` set. New code never prints; reports return text.
