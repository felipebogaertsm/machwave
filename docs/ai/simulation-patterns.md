# Simulation patterns

How the time-marched loop, the per-step state and the numerical methods fit together.
Read this before editing `machwave/simulation`, `machwave/core/solvers` or
`machwave/models/grain/fmm`.

## Per-step state

- Each engine type has a `MotorState` subclass (`machwave/simulation/solid/states.py`,
  `machwave/simulation/biliquid/states.py`) whose `run_timestep` appends one entry per
  step to each history list, and `build_result` freezes them into a `SimulationResult`.
- Every `MotorState` keeps the same step order, list names and array conventions. A
  change to one is mirrored in the other unless the physics differs.
- Loss components receive a `TimestepConditions` snapshot in SI units, never the state
  object. The snapshot may carry fields no current consumer reads; they are deliberate
  extension seams, not dead code.

## Order of accuracy

- The order stated for a coupled scheme is the global order of the whole loop, not the
  order of its inner solver.
- The chamber pressure is integrated with RK4 (`machwave/core/solvers/rk4.py`), but in
  the solid loop the web distance still advances with explicit Euler, so that loop is
  first order overall. Do not describe it as fourth order.

## Resolution and time step

- Resolution floors and default time steps (`MINIMUM_GRID_RESOLUTION` and
  `DEFAULT_GRID_RESOLUTION` in `machwave/models/grain/fmm/base.py`, `MAX_TIME_STEP` in
  `machwave/simulation/base.py`) come from convergence studies. Never lower one for
  speed; change it only with a new convergence study.

## Cost

- Loop cost is dominated by external solver calls (CEA, CoolProp). Measure a change by
  counting them, then by timing `make benchmark`.
- Thermochemical properties are cached on chamber pressure and mixture ratio rounded to
  `CHAMBER_PRESSURE_QUANTIZATION_PA` and `MIXTURE_RATIO_QUANTIZATION`
  (`machwave/models/propellants/categories/base.py`). A cache keyed on a raw float never
  hits; quantize the key the same way.
