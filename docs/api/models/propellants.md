# models.propellants

Propellant definition and thermochemical evaluation. A propellant is built from `PropellantComponent` instances (each with a chemical formula, density, enthalpy, and role), then evaluated at operating conditions via NASA CEA to obtain γ, molecular weight, adiabatic flame temperature, Isp, and condensed-phase fractions.

Submodules:

- [categories](propellants/categories.md) — `SolidPropellant` (with St. Robert’s burn rate law) and `BiliquidPropellant` (with O/F ratio)
- [formulations](propellants/formulations.md) — Ready-to-use propellant instances and JSON loader

::: machwave.models.propellants
