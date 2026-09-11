# core.mass_balance

Right-hand side of the chamber-pressure ODE solved during internal-ballistics
simulation, shared by the solid-motor and biliquid-engine state integrations.
The caller supplies \(\dot{m}_{in}\) (propellant regression for a solid motor,
summed injector flows for a biliquid engine) as a callable evaluated at each
Runge-Kutta stage pressure.

The control-volume balance behind it is derived in
[Mass Balance](../../explanations/mass_balance.md).

::: machwave.core.mass_balance
