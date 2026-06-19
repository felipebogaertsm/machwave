# 1. Thrust and Performance

Machwave calculates the **thrust** of a rocket motor/engine using the **thrust coefficient formulation**, which is derived from the idealized flow through a rocket nozzle.
The ideal thrust coefficient is calculated and multiplied by the **nozzle efficiency** to obtain the real thrust coefficient.
The nozzle efficiency accounts for the deviations from the idealized assumptions, such as boundary layer losses, chemical kinetic losses, and more.

## 1.1 Thrust Coefficient

$$
F = C_f\, P_0\, A_t
$$

(Sutton & Biblarz, Eq. 3-31)

where:

- $F$ is the thrust [N]
- $C_f$ is the thrust coefficient (dimensionless)
- $P_0$ is the chamber stagnation pressure [Pa]
- $A_t$ is the nozzle throat area [m$^2$]

Implemented in [`get_thrust_from_thrust_coefficient`][machwave.core.compressible_flow.nozzle.get_thrust_from_thrust_coefficient].

## 1.2 Ideal Thrust Coefficient

The **ideal thrust coefficient** is given by:

$$
C_{f,\text{ideal}} = \sqrt{\frac{2k_e^2}{k_e-1}\left(\frac{2}{k_e+1}\right)^{(k_e+1)/(k_e-1)}\!\left[1-\left(\frac{P_e}{P_0}\right)^{(k_e-1)/k_e}\right]} + \varepsilon\,\frac{P_e - P_\text{ext}}{P_0}
$$

(Sutton & Biblarz, Eq. 3-30)

where:

- $k_e$ is the exhaust isentropic exponent (dimensionless)
- $P_e$ is the exit pressure [Pa]
- $P_\text{ext}$ is the external (ambient) pressure [Pa]
- $\varepsilon$ is the expansion ratio (dimensionless)

The momentum term and the pressure term are returned separately by [`get_ideal_thrust_coefficient_components`][machwave.core.compressible_flow.nozzle.get_ideal_thrust_coefficient_components].
This way, nozzle losses can act on either term separately.

## 1.3 Flow Separation

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

## 1.4 Nozzle Efficiency

Real nozzles deviate from the ideal assumptions baked into the ideal thrust coefficient.
Machwave lumps these deviations into a single **nozzle efficiency** $\eta_\text{nozzle}$ applied multiplicatively to the ideal coefficient:

$$
C_{f} = \eta_\text{nozzle}\, C_{f,\text{ideal}}
$$

$$
\eta_\text{nozzle} = 1 - \sum_i \eta_i
$$

where each $\eta_i$ is a loss fraction accounting for one or more of the idealized assumptions.
Which and how many losses are included depends on the motor/engine category.

Each loss is composed by the motor's nozzle loss model and may derate the momentum term, the pressure term, or both of the thrust coefficient; the equation above is the case where every loss derates both terms.

## 1.5 Total Impulse and Specific Impulse

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
- $m_{prop}$ is the initial propellant mass [kg]
- $g_0 = 9.80665\ \text{m/s}^2$ is the standard gravitational acceleration

Implemented in
[`get_specific_impulse`][machwave.core.performance.get_specific_impulse].

# References

1. Sutton, G. P., & Biblarz, O. (2001). *Rocket Propulsion Elements* (7th ed.). Wiley. Ch. 2-3.
2. Summerfield, M., Foster, C. R., & Swan, W. C. (1954). Flow separation in overexpanded supersonic exhaust nozzles. *Jet Propulsion*, 24(5), 319-321.
