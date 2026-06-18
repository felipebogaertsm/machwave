# 3. Nozzle Losses

The ideal thrust coefficient $C_f$ derived in §1.2 assumes isentropic, perfectly expanded, single-phase, axially directed flow.
Real nozzles deviate from this ideal due to four independent loss mechanisms.
Each is expressed as a **percentage loss** and combined into an overall nozzle efficiency $\eta_{nozzle}$.

*All empirical correlations are from:*
*Coats et al. (1975). A Computer Program for the Prediction of Solid Propellant Rocket Motor Performance, Vol. I. AFRPL-TR-75-36 (DTIC AD-A015 140).*

## 3.1 Divergent Loss

A conical nozzle exhausts gas over a range of directions from $0$ to the half-angle $\alpha$ relative to the thrust axis.
The **axial momentum fraction** is computed by integrating over the cone surface, assuming uniform flow across the exit plane:

$$
\lambda = \frac{\int_0^\alpha \cos\theta\,2\pi\sin\theta\,d\theta}
               {\int_0^\alpha 2\pi\sin\theta\,d\theta}
= \frac{\left[\frac{\sin^2\theta}{2}\right]_0^\alpha}{[-\cos\theta]_0^\alpha}
= \frac{1 + \cos\alpha}{2}
$$

where:

- $\alpha$ is the nozzle divergence half-angle [deg]
- $\lambda$ is the axial momentum fraction (dimensionless)

The divergence loss is $1 - \lambda$, expressed as a fraction in [0, 1]:

$$
\boxed{\eta_{div} = \tfrac{1}{2}\,(1-\cos\alpha)}
$$

Applicable to **conical nozzles only**.
Contoured (bell) nozzles can achieve near-zero divergence loss by design.
Implemented in
[`get_nozzle_divergent_loss_fraction`][machwave.models.nozzle_losses.components.divergent.get_nozzle_divergent_loss_fraction].

*Applies to: solid and biliquid motors.*

## 3.2 Kinetics Loss

In the ideal $C_f$ derivation, the combustion products are assumed to remain in **shifting chemical equilibrium** as they expand through the nozzle.
In reality, finite-rate chemistry "freezes" the composition at some point, leaving unreacted species that carry energy out of the nozzle without contributing to thrust.

The magnitude is proportional to the gap between CEA-predicted frozen and equilibrium (shifting) specific impulses:

$$
\eta_{kin} = 0.333\left(1 - \frac{I_{sp,frozen}}{I_{sp,shifting}}\right) \times f_P
$$

where the pressure correction factor accounts for the fact that higher chamber pressures accelerate reactions toward equilibrium:

$$
f_P = \begin{cases} 1 & P_0 < 200\ \text{psi} \\ \dfrac{200}{P_0[\text{psi}]} & P_0 \geq 200\ \text{psi} \end{cases}
$$

where:

- $\eta_{kin}$ is the kinetics loss fraction (dimensionless)
- $I_{sp,frozen}$ and $I_{sp,shifting}$ are the CEA frozen- and shifting-equilibrium specific impulses at the same expansion ratio [s]
- $f_P$ is the pressure correction factor (dimensionless)
- $P_0$ is the chamber pressure [psi]

Implemented in
[`get_kinetics_loss_fraction`][machwave.models.nozzle_losses.components.spp1975.get_kinetics_loss_fraction].

*Applies to: solid and biliquid motors.*

## 3.3 Boundary Layer Loss

Viscous effects near the nozzle wall create a low-velocity **boundary layer** that reduces the effective flow area and transfers heat from the gas to the wall.
The governing parameter group emerges from Blasius flat-plate boundary-layer theory: the displacement thickness scales as $\delta^* \propto P_0^{0.8} / D_t^{0.2}$ (from a Reynolds-number argument with viscosity $\propto T^{0.7}$).

The loss is also time-dependent: the wall heats up during the burn, reducing the heat-flux driving force and therefore the loss:

$$
\eta_{BL} = 0.01 \cdot C_1\frac{P_0^{0.8}}{D_t^{0.2}}
\left[1 + 2\exp\!\left(-\frac{C_2\, P_0^{0.8}\, t}{D_t^{0.2}}\right)\right]
\left[1 + 0.016\,(\varepsilon - 9)\right]
$$

where:

- $\eta_{BL}$ is the boundary-layer loss fraction (dimensionless)
- $C_1$ and $C_2$ are empirical nozzle-material constants (e.g. $C_1 = 0.003650$, $C_2 = 0.000937$ for a standard graphite/phenolic nozzle)
- $P_0$ is the chamber pressure [psi]
- $D_t$ is the throat diameter [in]
- $t$ is the time from ignition [s]
- $\varepsilon$ is the expansion ratio (dimensionless)

The 0.01 factor converts the classical percent-form expression to the fraction convention used here.
Implemented in
[`get_boundary_layer_loss_fraction`][machwave.models.nozzle_losses.components.spp1975.get_boundary_layer_loss_fraction].

*Applies to: solid motors only* (the empirical constants $C_1, C_2$ are calibrated against a BATES motor; the biliquid engine state passes $\eta_{BL} = 0$).

## 3.4 Two-Phase Flow Loss

Solid and hybrid propellants produce **condensed-phase particles** (e.g. alumina $\text{Al}_2\text{O}_3$) in the combustion products.
These particles cannot expand isentropically through the nozzle and lag behind the gas, transferring momentum and heat imperfectly to the surrounding gas.

**Step 1 — Average particle size** (condensation in chamber + coagulation in nozzle):

$$
d_p = 0.454\;P_0^{1/3}\;\xi^{1/3}
      \left(1 - e^{-0.004 L^*}\right)
      \left(1 + 0.045\,D_t\right) \quad [\mu\text{m}]
$$

where:

- $d_p$ is the average condensed-phase particle diameter [$\mu$m]
- $\xi$ is the condensed-phase mass fraction (dimensionless)
- $L^*$ is the characteristic chamber length [in]
- $D_t$ is the throat diameter [in]
- $P_0$ is the chamber pressure [psi]

**Step 2 — Two-phase loss** (tabulated power-law fit):

$$
\eta_{2p} = 0.01 \cdot C_3\,\frac{\xi^{C_4}\,d_p^{C_5}}{P_0^{0.15}\,\varepsilon^{0.08}\,D_t^{C_6}}
$$

where:

- $\eta_{2p}$ is the two-phase flow loss fraction (dimensionless)
- $C_3$–$C_6$ are tabulated fit coefficients set by the $\xi$, $D_t$, and $d_p$ ranges (AFRPL-TR-75-36)
- $\varepsilon$ is the expansion ratio (dimensionless)

The 0.01 factor converts the percent-form expression to the fraction convention used here.
Implemented in
[`get_two_phase_flow_loss_fraction`][machwave.models.nozzle_losses.components.spp1975.get_two_phase_flow_loss_fraction].

*Applies to: solid motors only.*
Biliquid propellants typically produce gas-phase products with no condensed phase, so the biliquid engine state passes $\eta_{2p} = 0$.

## 3.5 Overall Nozzle Efficiency

The four loss fractions are additive, giving the overall efficiency applied to the ideal thrust coefficient:

$$
\boxed{\eta_{nozzle} = 1 - \left(\eta_{div} + \eta_{kin} + \eta_{BL} + \eta_{2p} + \eta_{other}\right)}
$$

$$
C_{f,real} = \eta_{nozzle}\,C_{f,ideal}
$$

where:

- $\eta_{nozzle}$ is the overall nozzle efficiency (dimensionless)
- $\eta_{other}$ is any additional, user-specified loss fraction (dimensionless)
- $C_{f,ideal}$ and $C_{f,real}$ are the ideal and real thrust coefficients (dimensionless)

Each loss is a [`LossComponent`][machwave.models.nozzle_losses.LossComponent] that derates the momentum term, the pressure term, or both of the decoupled thrust coefficient — the nozzle divergence loss derates the momentum term only.
The components are composed by [`NozzleLossModel`][machwave.models.nozzle_losses.NozzleLossModel], owned by the motor; when every loss derates both terms this reduces to the scalar form above.

# References

1. Coats, D. E., Levine, J. N., Nickerson, G. R., Tyson, T. J., Cohen, N. S., Harry, D. P. III, & Price, C. F. (1975). *A Computer Program for the Prediction of Solid Propellant Rocket Motor Performance, Volume I*. Technical Report AFRPL-TR-75-36 (DTIC Accession AD-A015 140). Air Force Rocket Propulsion Laboratory.
