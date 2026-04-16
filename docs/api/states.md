# States

Motor operation state tracking. Each motor type has a corresponding state class (`SolidMotorState`, `LiquidEngineState`) that accumulates time-series data during simulation: chamber pressure, exit pressure, thrust, Cf, propellant mass, and efficiency breakdown (divergent, kinetics, boundary layer, two-phase losses).

Solid motor states also track grain regression (web distance, burn area, volume), propellant CoG, and moment-of-inertia tensors over time. Liquid engine states additionally store tank pressures and propellant masses per tank.

::: machwave.states
