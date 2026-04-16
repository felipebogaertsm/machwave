# models.feed_systems

Feed system models for liquid rocket engines. Defines how propellant is delivered from tanks to the combustion chamber.

The base `FeedSystem` class abstracts mass flow rate and tank pressure calculations. `StackedTankPressureFedFeedSystem` implements a pressure-fed configuration with oxidizer and fuel lines, accounting for line losses and piston pressure drops.

See [tanks](feed_systems/tanks.md) for the tank thermodynamic model.

::: machwave.models.feed_systems
