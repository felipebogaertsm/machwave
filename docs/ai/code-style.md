# Code style

Applies to every Python file in `machwave/`, `tests/`, `examples/` and `scripts/`.
`make check` enforces formatting, linting and types; the rules below are what review
enforces beyond the tools.

## Names

A name is the first documentation. If a reader needs a comment to know what a value is,
the name is wrong.

- State meaning in domain terms, fully spelled: `chamber_pressure`,
  `isentropic_exponent`, `time_step`, `burn_area`.
- A propulsion engineer must understand every public name without reading the code.
  Public functions, attributes, result fields and exported column names get the most care.
- Mathematical symbols stay in the docstring, not in the name. The docstring maps each
  argument to its symbol and equation. A short local symbol is acceptable only inside a
  function that transcribes one cited equation.
- Functions and methods are verbs (`get_`, `compute_`, `solve_`). Properties and
  attributes are nouns. Booleans read as predicates (`is_choked`, `has_inhibited_ends`).
- One word per concept everywhere. If the solid motor state says `chamber_pressure`, so do
  the biliquid state, the results, the plots and the docs.
- No empty words: `data`, `info`, `value`, `obj`, `item`, `manager`, `helper`, `_list`.
  No `utils` or `helpers` modules; a module is named for what it does.
- Flags are keyword-only arguments or enumerations, never positional booleans.
- Physical and numerical constants are named module constants, never bare numbers in
  expressions.
- Never plan to fix a bad name later. Choose it well now.

## Do not abbreviate

Spell words out in identifiers, file and module names, docstrings, comments, commits and
pull requests: `figure`, `error`, `index`, `step_count`, `minimum_value`,
`center_of_gravity`, `moment_of_inertia`, `specific_impulse`, `klemmung`,
`oxidizer_to_fuel_ratio`. Physics shorthand such as `k`, `d_t`, `Isp`, `Kn`, `Cf` or
`m_dot` is not an exception.

The exceptions are this closed list. Anything not on it is spelled out.

| Exception | Allowed forms | Condition |
| --- | --- | --- |
| Language and framework names | `self`, `cls`, `args`, `kwargs`, `dtype`, `ndarray`, dunder methods, pytest fixtures such as `tmp_path` | Names fixed by Python, NumPy or pytest |
| Third-party import aliases | `np` (NumPy), `npt` (NumPy typing), `go` (Plotly graph objects) | Only these; Machwave modules keep spelled-out aliases such as `grain_models` |
| Environment and tooling | `env`, `.env`, `venv`, `dev`, `docs`, `src`, `ci`, `os`, `sys` | Directories, files, dependency groups and tooling |
| Proper names | CEA, CoolProp, NIST, `.eng`, JSON, CSV, URL, ID, API | Names of external programs, formats or organizations, not of concepts |
| Unit symbols | `pa`, `mpa`, `psi`, `mm`, `kg`, `s` | Only as a unit suffix (`pressure_psi`) or in conversion function names |
| Mathematical method names | `rk4`, `ode`, `2d`, `3d` | The established name of a method or dimension |
| Short-scope indices and coordinates | `i`, `j`; `x`, `y`, `z` | Loop indices within a few lines; Cartesian coordinates |
| Minimum and maximum prefixes | `min_`, `max_` | As in `max_iterations` |

## Comments and docstrings

- Before writing a comment, try a better name or an extracted function. Keep a comment
  only for a reason the code cannot state: a physical assumption, a numerical stability
  limit, the source of an equation.
- Never comment what the code does, the history of a change or a tracker reference.
- Docstrings use `Args:`, `Returns:` and `Raises:` sections, as the docstring rules in
  `pyproject.toml` require, with the SI unit of every physical quantity.
- Keep docstrings short and objective; one line when one line is enough. Do not write a
  docstring that only restates the name.
- Physical models add a `References:` section; see
  [physical-models.md](physical-models.md).
- Docstring prose wraps at 88 characters. Ruff does not flag long docstring lines, so
  check with `awk 'length > 88'` on the files you touched.

## Imports

- Namespace imports: `import machwave.models.grain as grain_models`. When a local name
  would shadow the module, alias the import (`import machwave.core.compressible_flow.nozzle
  as nozzle_core`); never switch to `from module import name` to dodge the clash.
- Optional dependencies go through `machwave/common/extras.py`: modules reached only when
  a feature is used guard their own import and raise `MissingOptionalDependencyError`;
  modules on the import path use `extras.require`.
- Imports that would go up the layer order stay under `typing.TYPE_CHECKING`.

## Units

- Everything inside the package is SI and carries no unit suffix.
- A value in any other unit says so in its name (`pressure_psi`,
  `burn_rate_coefficient_imperial`).
- Every conversion calls a function in `machwave/core/conversions.py`, in package code,
  tests and examples alike. Conversion functions are kept even when only tests call them.

## Errors, warnings and logging

| Channel | Used for | Rule |
| --- | --- | --- |
| Exception | Invalid input or a failed operation | Raise the most specific Machwave exception. The message names the quantity, its value with units and the allowed range. Chain with `raise ... from error` |
| `warnings.warn` | Execution continues but the user should act: a model used outside its valid range, a fallback, a deprecation | Use a dedicated warning class and set `stacklevel` so the warning points at the caller |
| `logging.getLogger(__name__)` | Diagnostics the user opts into | `DEBUG` for solver detail, `INFO` for milestones such as burnout. Never configure handlers or levels in the package |
| Return values | Reports and summaries | Return text or objects; only examples and scripts print |

## Simplicity

- No speculative generality: build what the issue needs, reuse what the package already
  has, then the standard library, then an installed dependency, and only then new code.
- Deep modules over thin wrappers. A function or class must hide more than it exposes;
  remove pass-through wrappers.
- Consistency first: a new module follows the nearest existing pattern. A better pattern
  is applied everywhere in its own change, never in one place only.
- A new dependency needs a reason in the pull request and goes in an optional extra unless
  the core needs it.
- Correct first, then clear, then fast. Optimize only with a measurement.
