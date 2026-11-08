# Thrust and Performance

Machwave calculates the **thrust** of a rocket motor/engine using the **thrust coefficient formulation**, which is derived from the idealized flow through a rocket nozzle.
The ideal thrust coefficient has two terms, a momentum term which dominates and a pressure term.
Each term is calculated and multiplied by the **nozzle efficiency** to obtain the real thrust coefficient.
The nozzle efficiency can be applied independently to each term, and accounts for the deviations from the idealized assumptions, such as boundary layer losses, chemical kinetic losses, and more.

## Thrust Coefficient

$$
F = C_f\, P_0\, A_t
$$

(Sutton & Biblarz, Eq. 3-31)

where:

- $F$ is the thrust [N]
- $C_f$ is the thrust coefficient (dimensionless)
- $P_0$ is the chamber stagnation pressure [Pa]
- $A_t$ is the effective nozzle throat area [m$^2$]

Implemented in [`get_thrust_from_thrust_coefficient`][machwave.core.compressible_flow.nozzle.get_thrust_from_thrust_coefficient].

The effective nozzle throat area is modeled as the product of the geometric throat area with the discharge coefficient:

$$
A_t = C_d\, A_{t,\text{geo}}
$$

where:

- $C_d$ is the throat discharge coefficient (dimensionless)
- $A_{t,\text{geo}}$ is the geometric nozzle throat area [m$^2$]

A throat discharge loss therefore reduces thrust along with mass outflow.

Implemented in [`get_effective_nozzle_throat_area`][machwave.core.compressible_flow.nozzle.get_effective_nozzle_throat_area].

## Ideal Thrust Coefficient

The **ideal thrust coefficient** is given by:

$$
C_{f,\text{ideal}} = \underbrace{\sqrt{\frac{2k_e^2}{k_e-1}\left(\frac{2}{k_e+1}\right)^{(k_e+1)/(k_e-1)}\!\left[1-\left(\frac{P_e}{P_0}\right)^{(k_e-1)/k_e}\right]}}_{\text{momentum term}} + \underbrace{\varepsilon\,\frac{P_e - P_\text{ext}}{P_0}}_{\text{pressure term}}
$$

(Sutton & Biblarz, Eq. 3-30)

where:

- $k_e$ is the exhaust isentropic exponent, distinct from the chamber value (see [Propellants](propellants.md#chamber-and-exhaust-properties)) (dimensionless)
- $P_e$ is the exit pressure [Pa]
- $P_\text{ext}$ is the external (ambient) pressure [Pa]
- $\varepsilon$ is the expansion ratio (dimensionless)

The momentum term and the pressure term are returned separately by [`get_ideal_thrust_coefficient_terms`][machwave.core.compressible_flow.nozzle.get_ideal_thrust_coefficient_terms].
This way, nozzle losses can act on either term separately.

## Flow Separation

The ideal thrust coefficient above assumes the nozzle flows full, with the exhaust attached to the wall all the way to the geometric exit.
As the chamber pressure decays during tail-off the nozzle becomes increasingly overexpanded ($P_e \ll P_\text{ext}$), and below a threshold the boundary layer can no longer sustain the adverse pressure gradient.
The flow then separates from the wall upstream of the geometric exit, shrinking the effective exit area and pinning the realized exit pressure near the separation pressure.

Machwave applies a simple **Summerfield criterion**: separation occurs once the isentropic exit pressure drops below a fixed fraction of the ambient pressure,

$$
P_e < P_\text{sep} = f_\text{sep}\, P_\text{ext}, \qquad f_\text{sep} \approx 0.4
$$

Past that point the **effective expansion ratio** $\varepsilon_\text{eff}$ is the area ratio at which the isentropic wall pressure equals $P_\text{sep}$, and both $\varepsilon_\text{eff}$ and $P_\text{sep}$ feed the ideal thrust coefficient in place of the geometric values.
This bounds the pressure-thrust term so tail-off thrust decays smoothly toward zero instead of diverging negative.

where:

- $P_\text{sep}$ is the separation pressure [Pa]
- $f_\text{sep}$ is the separation-to-ambient pressure ratio (dimensionless)
- $\varepsilon_\text{eff}$ is the effective expansion ratio at separation (dimensionless)

Implemented in [`get_separated_exit_conditions`][machwave.core.compressible_flow.nozzle.get_separated_exit_conditions].

## Nozzle Efficiency and Term Targets

Real nozzles deviate from the idealized assumptions baked into the ideal thrust coefficient.
Rather than applying an arbitrary lump-sum penalty, Machwave decouples the thrust coefficient into its **momentum** and **pressure** terms, evaluates each loss component against its specific target, and combines the resulting corrections into the realized nozzle efficiency $\eta_\text{nozzle}$.

Implemented in [`NozzleLossModel`][machwave.models.nozzle_losses.base.NozzleLossModel] and [`ThrustCoefficientTermTarget`][machwave.models.nozzle_losses.base.ThrustCoefficientTermTarget].

### Decoupled Thrust Coefficient Terms

The ideal thrust coefficient is partitioned as:

$$
C_{f,\text{ideal}} = C_{f,\text{mom,ideal}} + C_{f,\text{pres,ideal}}
$$

where $C_{f,\text{mom,ideal}}$ is the momentum term and $C_{f,\text{pres,ideal}} = \varepsilon\,\frac{P_e - P_\text{ext}}{P_0}$ is the pressure term.

Each loss component targets one or both terms via [`ThrustCoefficientTermTarget`][machwave.models.nozzle_losses.base.ThrustCoefficientTermTarget]:

- `MOMENTUM`: derates the momentum term only.
- `PRESSURE`: derates the pressure term only.
- `BOTH`: derates both momentum and pressure terms simultaneously.

### Accumulating Loss Factors

During each timestep, each active component computes its non-dimensional loss fraction $\eta_i \in [0, 1]$.
Machwave sums these fractions into distinct correction factors for the momentum and pressure terms:

$$
f_\text{mom} = 1 - \sum_{i \in \mathcal{L}_\text{mom}} \eta_i
$$

$$
f_\text{pres} = 1 - \sum_{i \in \mathcal{L}_\text{pres}} \eta_i
$$

where $\mathcal{L}_\text{mom}$ and $\mathcal{L}_\text{pres}$ are the sets of loss components that affect the momentum and pressure terms, respectively.
If either $f_\text{mom} < 0$ or $f_\text{pres} < 0$, an error is raised because losses cannot derate a term below zero.

The corrected thrust coefficient terms are:

$$
C_{f,\text{mom}} = f_\text{mom} \, C_{f,\text{mom,ideal}}
$$

$$
C_{f,\text{pres}} = f_\text{pres} \, C_{f,\text{pres,ideal}}
$$

and the total delivered thrust coefficient is their sum:

$$
C_f = C_{f,\text{mom}} + C_{f,\text{pres}}
$$

### Combined Nozzle Efficiency

The effective nozzle efficiency $\eta_\text{nozzle}$ represents the ratio between delivered and ideal thrust coefficients:

$$
\eta_\text{nozzle} = \frac{C_f}{C_{f,\text{ideal}}} = \frac{C_{f,\text{mom}} + C_{f,\text{pres}}}{C_{f,\text{mom,ideal}} + C_{f,\text{pres,ideal}}}
$$

When all components target `BOTH` (such as flat-efficiency models or kinetics without divergence loss), $f_\text{mom} = f_\text{pres} = 1 - \sum_i \eta_i$, which recovers the familiar scalar efficiency:

$$
\eta_\text{nozzle} = 1 - \sum_i \eta_i
$$

However, when components target specific terms (e.g. geometric divergence acting exclusively on exit momentum), $\eta_\text{nozzle}$ becomes a weighted average of $f_\text{mom}$ and $f_\text{pres}$ weighted by their respective ideal terms.

**Overexpansion guard:** Under extreme overexpansion during tail-off ($P_e \ll P_\text{ext}$), a large negative pressure term can nearly cancel out the momentum term, driving $C_{f,\text{ideal}} \to 0$ and causing the efficiency fraction to diverge.
When $C_{f,\text{ideal}} \le 10^{-9}$, Machwave defines nozzle efficiency purely by the momentum factor:

$$
\eta_\text{nozzle} = f_\text{mom} \quad \text{for } C_{f,\text{ideal}} \le 10^{-9}
$$

### How Loss Components Act on the Terms

Machwave provides several standard loss components across solid and liquid motors:

1. **Divergence Loss ([`DivergentLoss`][machwave.models.nozzle_losses.components.divergent.DivergentLoss])**:
   - **Target:** `MOMENTUM`.
   - **Mechanism:** In a conical convergent-divergent nozzle with half-angle $\alpha$, exhaust gases exit with non-axial velocity components. The momentum efficiency factor is $\lambda = \frac{1 + \cos\alpha}{2}$, giving a loss fraction $\eta_\text{div} = \frac{1 - \cos\alpha}{2}$. Because this non-axial flow affects only the exit momentum vector and does not alter the integrated exit static pressure, it derates momentum and spares the pressure term.

2. **Boundary Layer Loss ([`BoundaryLayerLoss`][machwave.models.nozzle_losses.components.spp1975.BoundaryLayerLoss])**:
   - **Target:** `BOTH`.
   - **Mechanism:** Viscous wall shear reduces core gas velocity and exit momentum, while boundary layer displacement thickness reduces the effective expansion area and modifies the wall static pressure distribution. Derived from the empirical SPP-75 solid nozzle correlation with time and pressure dependence.

3. **Chemical Kinetics Loss ([`KineticsLoss`][machwave.models.nozzle_losses.components.spp1975.KineticsLoss])**:
   - **Target:** `BOTH`.
   - **Mechanism:** Rapid expansion through supersonic nozzles limits residence time, preventing chemical recombination of dissociated gas species (shifting vs. frozen equilibrium). This reduces sensible heat conversion into kinetic energy and lowers expansion pressure throughout the nozzle.

4. **Two-Phase Flow Loss ([`TwoPhaseFlowLoss`][machwave.models.nozzle_losses.components.spp1975.TwoPhaseFlowLoss])**:
   - **Target:** `BOTH`.
   - **Mechanism:** Solid or liquid condensed particles (such as alumina $\text{Al}_2\text{O}_3$ in metallized solid propellants) exhibit velocity lag (drag) and thermal lag behind the gas phase. This momentum drag and non-equilibrium heat transfer degrade both exit momentum and expansion pressure.

5. **Constant Fraction Loss ([`ConstantFractionLoss`][machwave.models.nozzle_losses.components.constant.ConstantFractionLoss])**:
   - **Target:** `BOTH`.
   - **Mechanism:** Represents fixed parasitic margins or lumped losses (such as submerged nozzle losses or entrance losses) applied uniformly across the entire thrust coefficient.

## Total Impulse and Specific Impulse

After the thrust is calculated, the total impulse is obtained by integrating it over the thrust time:

$$
I_{total} = \int_0^{t_{thrust}} F\,dt
$$

where:

- $I_{total}$ is the total impulse [N-s]
- $t_{thrust}$ is the total thrust time [s]

Machwave integrates the discrete thrust-time trace numerically.

Implemented in
[`get_total_impulse`][machwave.core.performance.get_total_impulse].

Finally, the **specific impulse** measures the impulse delivered per unit weight of propellant consumed:

$$
I_{sp} = \frac{I_{total}}{m_{prop}\,g_0} \quad [\text{s}]
$$

where:

- $I_{sp}$ is the specific impulse [s]
- $m_{prop}$ is the propellant mass expelled over the run [kg]
- $g_0 = 9.80665\ \text{m/s}^2$ is the standard gravitational acceleration

Implemented in
[`get_specific_impulse`][machwave.core.performance.get_specific_impulse].

# References

1. Sutton, G. P., & Biblarz, O. (2001). *Rocket Propulsion Elements* (7th ed.). Wiley. Ch. 2-3.
2. Summerfield, M., Foster, C. R., & Swan, W. C. (1954). Flow separation in overexpanded supersonic exhaust nozzles. *Jet Propulsion*, 24(5), 319-321.
