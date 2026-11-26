# Simulation patterns

Rules for the time-marched loop and the numerical methods in `machwave/simulation`,
`machwave/core/solvers` and `machwave/models/grain/fmm`.

## Per-step state

- The solid and biliquid `MotorState` subclasses keep the same step order, history list
  names and array conventions. A change to one is mirrored in the other unless the
  physics differs.
- `TimestepConditions` may carry fields no current consumer reads. They are deliberate
  extension seams; do not remove them as dead code.

## Order of accuracy

- The order stated for a coupled scheme is the global order of the loop, not the order of
  its inner solver.
- In the solid loop the chamber pressure uses RK4 but the web distance advances with
  explicit Euler, so the loop is first order overall.

## Resolution and time step

- `MINIMUM_GRID_RESOLUTION` and `DEFAULT_GRID_RESOLUTION`
  (`machwave/models/grain/fmm/base.py`) and `MAX_TIME_STEP`
  (`machwave/simulation/base.py`) come from convergence studies. Never lower one for
  speed; change it only with a new convergence study.

## Cost

- Loop cost is dominated by CEA and CoolProp calls. Optimize only with a measurement:
  count those calls, then time `make benchmark`.
- A cache keyed on a raw float never hits. Quantize the key, as the thermochemistry
  cache does with `CHAMBER_PRESSURE_QUANTIZATION_PA` and `MIXTURE_RATIO_QUANTIZATION`
  (`machwave/models/propellants/categories/base.py`).
