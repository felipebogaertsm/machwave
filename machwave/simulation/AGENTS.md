# machwave/simulation

Time marching states, simulations and results. Read
[docs/ai/simulation.md](../../docs/ai/simulation.md) before editing.

- Keep `SolidMotorState` and `BiliquidEngineState` structurally parallel; a change to one
  `run_timestep` is checked against the other.
- `TimestepConditions` fields that no component reads yet are intentional.
- Results expose arrays and derived quantities; formatting for people stays in reports
  that return text.
