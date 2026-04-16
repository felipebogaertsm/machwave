# models.motors

Top-level motor/engine definitions that assemble all physical sub-components into a complete propulsion unit.

- `SolidMotor` — Combines a `Grain`, `SolidPropellant`, and `SolidMotorThrustChamber`. Provides launch/dry mass, free chamber volume, CoG (mass-weighted across grain and hardware), and thrust coefficient with loss corrections.
- `LiquidEngine` — Combines a `BiliquidPropellant`, `LiquidEngineThrustChamber`, and `FeedSystem`. Tracks CoG shift as propellant is consumed from the tanks.

Both inherit from the generic `Motor[P, T]` base class. A motor instance is the primary input to `InternalBallisticsSimulation`.

::: machwave.models.motors
