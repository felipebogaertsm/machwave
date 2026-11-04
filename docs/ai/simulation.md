# Simulation

Applies to `machwave/simulation/`.

## Solid and biliquid states mirror each other

`SolidMotorState` (`machwave/simulation/solid/states.py`) and `BiliquidEngineState`
(`machwave/simulation/biliquid/states.py`) share one structure so that the `MotorState`
contract and the shared result handling treat them alike.

- Same `run_timestep` order: bind locals, derived geometry and mass, exit pressure,
  losses, thrust, end-of-burn check, end-of-thrust early return, advance the state.
- Same array conventions: `time` and `chamber_pressure` start with one element; derived
  arrays start empty.
- Parallel names wherever the physics maps cleanly.

When changing one state's `run_timestep` or initializer, apply the matching change to the
other. Differences are allowed only where the physics differs (grain geometry against tank
drain); differences in loss arrays, naming or end-of-burn timing are not.

## Timestep conditions are a deliberate snapshot

`TimestepConditions` (`machwave/simulation/states.py`) and its solid and biliquid
subclasses carry per-step quantities beyond what the current loss components read. The
unread fields and the per-engine split are intentional: a future loss correlation can read
more fields without changing the states. Do not remove them as unused.

## Time integration

- Chamber pressure is integrated by fourth-order Runge-Kutta within each time step.
- Grain web, burn area, free chamber volume and propellant masses advance outside that
  solver, so the coupled time step is first order overall. Do not describe the time
  marching as fourth order.
- A change to the time step must keep masses and pressures non-negative at every step,
  including the final step of a line or grain that runs out.

## Cost of the biliquid loop

The biliquid loop is dominated by chemical equilibrium evaluations, not fluid property
lookups. Results are cached on chamber pressure and mixture ratio quantized by
`CHAMBER_PRESSURE_QUANTIZATION_PA` and `MIXTURE_RATIO_QUANTIZATION`
(`machwave/models/propellants/categories/base.py`). Anything that visits more distinct
quantized states (a longer burn, a shifted mixture ratio) costs more time; measure with
`make benchmark` before and after a change to the loop.
