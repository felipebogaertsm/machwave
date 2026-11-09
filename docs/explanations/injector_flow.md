# Injector Flow

Machwave computes the mass flow of every injector element with **Dyer's non-homogeneous non-equilibrium model**.
It is the one orifice model of the biliquid path: a subcooled liquid, a saturated self-pressurizing propellant and everything in between flow through the same expression, and the right limit comes out of the pressures alone.

## Two Limits

The **single-phase incompressible** flow treats the propellant as a liquid all the way through the orifice:

$$
\dot{m}_{SPI} = C_d\, A \sqrt{2 \rho_1 (P_1 - P_2)}
$$

where $\rho_1$ and $P_1$ are the density and pressure at the injector face and $P_2$ is the chamber pressure.
It is exact for a liquid that stays above its vapor pressure, such as ethanol or kerosene against any chamber.
Saturated nitrous oxide flashes once its pressure drops below $P_v$ inside the orifice, the vapor takes volume the liquid would have occupied, and the incompressible flow overpredicts the measured one.

The **homogeneous equilibrium** flow takes the opposite view: the two phases stay in equilibrium and at the same velocity along an isentropic expansion from the inlet state:

$$
\dot{m}_{HEM} = C_d\, A\, \rho_2 \sqrt{2 (h_1 - h_2)}, \qquad s_2 = s_1
$$

The flux reaches a maximum at a pressure above the chamber, so the orifice chokes there, and the flow stops responding to the chamber pressure below it.
Bubbles take time to grow, and a short orifice does not give them that time, so the equilibrium flow underpredicts the measured one.

## The Blend

Dyer et al. weight the two by the ratio of the bubble growth time to the liquid residence time in the orifice:

$$
\dot{m} = \frac{\kappa}{1 + \kappa}\, \dot{m}_{SPI} + \frac{1}{1 + \kappa}\, \dot{m}_{HEM},
\qquad
\kappa = \sqrt{\frac{P_1 - P_2}{P_v - P_2}}
$$

A large $\kappa$ means the liquid leaves before its bubbles grow, and the flow is incompressible.
A small $\kappa$ means the bubbles grow before the liquid leaves, and the flow is at equilibrium.
A saturated inlet, $P_1 = P_v$, sits at $\kappa = 1$, the even blend.
Pressurant or a piston raise $P_1$ above $P_v$ and push the flow toward the incompressible limit; a feedline loss pulls $P_1$ below $P_v$ and pushes it toward equilibrium.

$\kappa$ is computed at every timestep from the inlet and chamber pressures, since all three pressures move through a burn: the tank cools and $P_v$ drops with it, the chamber follows the flow.

Where $P_v \le P_2$ nothing can flash in the orifice and the flow is the incompressible one.
Nitrous oxide at a tank temperature within a percent of its critical temperature still flows, but the saturated-liquid state the equilibrium term starts from is ill-conditioned there.
An inlet already below its vapor pressure is flashing in the feedline, and the vapor formed there goes unaccounted for.
A run reports both as a warning at their onset and keeps the time each line spent in them in the result.

## Calibration

The orifice length drops out of $\kappa$, yet a long orifice brings the liquid closer to equilibrium.
The **non-equilibrium factor** of an element multiplies $\kappa$ and is the knob to fit cold-flow data with, next to the discharge coefficient: below one for a long orifice, above one where the measured flow runs closer to incompressible.
The two are not separable from a single test point.
A water or subcooled cold flow fixes the discharge coefficient, since nothing flashes there, and a saturated cold flow then fixes the factor.
An infinite factor is the incompressible flow alone, taken without any fluid property lookup.

## Implementation

[`InjectorElement`][machwave.models.thrust_chamber.injector.InjectorElement] holds the discharge coefficient, the flow area and the non-equilibrium factor, and computes its flow with [`get_dyer_mass_flux`][machwave.core.two_phase_flow.get_dyer_mass_flux].
The equilibrium term is [`get_homogeneous_equilibrium_mass_flux`][machwave.core.two_phase_flow.get_homogeneous_equilibrium_mass_flux], which searches the isentrope for the choked flux with CoolProp.
[`BiliquidEngineState`][machwave.simulation.biliquid.states.BiliquidEngineState] tracks the time each line spends with its inlet below its vapor pressure and with its tank near the critical point, and [`BiliquidSimulationResult`][machwave.simulation.biliquid.results.BiliquidSimulationResult] carries both.

# References

1. Dyer, J., Doran, E., Dunn, Z., Lohner, K., Zilliac, G., & Cantwell, B. (2007). Modeling Feed System Flow Physics for Self-Pressurizing Propellants. *AIAA 2007-5702*.
2. Waxman, B. S., Zimmerman, J. E., Cantwell, B. J., & Zilliac, G. G. (2013). Mass Flow Rate and Isolation Characteristics of Injectors for Use with Self-Pressurizing Oxidizers in Hybrid Rockets. *AIAA 2013-3636*.
