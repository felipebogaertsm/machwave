# 4. Nozzle Losses

The ideal thrust coefficient \(C_f\) derived in §1.8 assumes isentropic, perfectly
expanded, single-phase, axially directed flow. Real nozzles deviate from this ideal
due to four independent loss mechanisms. Each is expressed as a **percentage loss**
and combined into an overall nozzle efficiency \(\eta_{nozzle}\).

*All empirical correlations are from:*  
*Coats et al. (1975). A Computer Program for the Prediction of Solid Propellant
Rocket Motor Performance, Vol. I. AFRPL-TR-75-36 (DTIC AD-A015 140).*

---

## 4.1 Divergent Loss

A conical nozzle exhausts gas over a range of directions from \(0\) to the
half-angle \(\alpha\) relative to the thrust axis. The **axial momentum fraction**
is computed by integrating over the cone surface, assuming uniform flow across the
exit plane:

\[
\lambda = \frac{\int_0^\alpha \cos\theta\,2\pi\sin\theta\,d\theta}
               {\int_0^\alpha 2\pi\sin\theta\,d\theta}
= \frac{\left[\frac{\sin^2\theta}{2}\right]_0^\alpha}{[-\cos\theta]_0^\alpha}
= \frac{1 + \cos\alpha}{2}
\]

The divergence loss in percent is \(1 - \lambda\), expressed as a percentage:

\[
\boxed{\eta_{div} = 50\,(1-\cos\alpha) \quad [\%]}
\]

Applicable to **conical nozzles only**. Contoured (bell) nozzles can achieve near-zero
divergence loss by design. Implemented in
[`get_nozzle_divergent_percentage_loss`][machwave.core.compressible_flow.losses.get_nozzle_divergent_percentage_loss].

---

## 4.2 Kinetics Loss

In the ideal \(C_f\) derivation, the combustion products are assumed to remain in
**shifting chemical equilibrium** as they expand through the nozzle. In reality,
finite-rate chemistry "freezes" the composition at some point, leaving unreacted
species that carry energy out of the nozzle without contributing to thrust.

The magnitude is proportional to the gap between CEA-predicted frozen and
equilibrium (shifting) specific impulses:

\[
\eta_{kin} = 33.3\left(1 - \frac{I_{sp,frozen}}{I_{sp,shifting}}\right) \times f_P \quad [\%]
\]

where the pressure correction factor accounts for the fact that higher chamber
pressures accelerate reactions toward equilibrium:

\[
f_P = \begin{cases} 1 & P_0 < 200\ \text{psi} \\ \dfrac{200}{P_0[\text{psi}]} & P_0 \geq 200\ \text{psi} \end{cases}
\]

Implemented in
[`get_kinetics_percentage_loss`][machwave.core.compressible_flow.losses.get_kinetics_percentage_loss].

---

## 4.3 Boundary Layer Loss

Viscous effects near the nozzle wall create a low-velocity **boundary layer** that
reduces the effective flow area and transfers heat from the gas to the wall. The
governing parameter group emerges from Blasius flat-plate boundary-layer theory:
the displacement thickness scales as \(\delta^* \propto P_0^{0.8} / D_t^{0.2}\)
(from a Reynolds-number argument with viscosity \(\propto T^{0.7}\)).

The loss is also time-dependent: the wall heats up during the burn, reducing the
heat-flux driving force and therefore the loss:

\[
\eta_{BL} = C_1\frac{P_0^{0.8}}{D_t^{0.2}}
\left[1 + 2\exp\!\left(-\frac{C_2\, P_0^{0.8}\, t}{D_t^{0.2}}\right)\right]
\left[1 + 0.016\,(\varepsilon - 9)\right] \quad [\%]
\]

with pressures in psi and diameter in inches. \(C_1\) and \(C_2\) are
nozzle-material constants (e.g. \(C_1=0.003650\), \(C_2=0.000937\) for a
standard graphite/phenolic nozzle). Implemented in
[`get_boundary_layer_percentage_loss`][machwave.core.compressible_flow.losses.get_boundary_layer_percentage_loss].

---

## 4.4 Two-Phase Flow Loss

Solid and hybrid propellants produce **condensed-phase particles** (e.g. alumina
\(\text{Al}_2\text{O}_3\)) in the combustion products. These particles cannot
expand isentropically through the nozzle and lag behind the gas, transferring
momentum and heat imperfectly to the surrounding gas.

**Step 1 — Average particle size** (condensation in chamber + coagulation in nozzle):

\[
d_p = 0.454\;P_0^{1/3}\;\xi^{1/3}
      \left(1 - e^{-0.004 L^*}\right)
      \left(1 + 0.045\,D_t\right) \quad [\mu\text{m}]
\]

where \(\xi\) is the condensed-phase mass fraction, \(L^*\) is the characteristic
chamber length [in], and \(D_t\) is the throat diameter [in].

**Step 2 — Two-phase loss** (tabulated power-law fit):

\[
\eta_{2p} = C_3\,\frac{\xi^{C_4}\,d_p^{C_5}}{P_0^{0.15}\,\varepsilon^{0.08}\,D_t^{C_6}} \quad [\%]
\]

Coefficients \(C_3\)–\(C_6\) depend on \(\xi\), \(D_t\), and \(d_p\) ranges
(tabulated in AFRPL-TR-75-36). Implemented in
[`get_two_phase_flow_percentage_loss`][machwave.core.compressible_flow.losses.get_two_phase_flow_percentage_loss].

---

## 4.5 Overall Nozzle Efficiency

The four losses are additive in percentage, giving the overall efficiency applied
to the ideal thrust coefficient:

\[
\boxed{\eta_{nozzle} = 1 - \frac{\eta_{div} + \eta_{kin} + \eta_{BL} + \eta_{2p} + \eta_{other}}{100}}
\]

\[
C_{f,real} = \eta_{nozzle}\,C_{f,ideal}
\]

Implemented in
[`get_overall_nozzle_efficiency`][machwave.core.compressible_flow.losses.get_overall_nozzle_efficiency]
and applied via
[`apply_thrust_coefficient_correction`][machwave.core.compressible_flow.nozzle.apply_thrust_coefficient_correction].

---

## References

1. Coats, D. E., Levine, J. N., Nickerson, G. R., Tyson, T. J., Cohen, N. S., Harry, D. P. III, & Price, C. F. (1975). *A Computer Program for the Prediction of Solid Propellant Rocket Motor Performance, Volume I*. Technical Report AFRPL-TR-75-36 (DTIC Accession AD-A015 140). Air Force Rocket Propulsion Laboratory.
2. Sutton, G. P., & Biblarz, O. (2017). *Rocket Propulsion Elements* (9th ed.). Wiley. Ch. 3.