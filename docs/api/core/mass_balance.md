# core.mass_balance

Right-hand side of the chamber-pressure ODE solved during internal-ballistics
simulation. A single control-volume mass balance covers both choked and
sub-critical nozzle flow (Seidel 1965, Eq. 35), and is shared by the solid-motor
and biliquid-engine state integrations — the caller supplies the appropriate
\(\dot{m}_{in}\) (propellant regression for a solid motor, summed injector flows
for a biliquid engine).

::: machwave.core.mass_balance
