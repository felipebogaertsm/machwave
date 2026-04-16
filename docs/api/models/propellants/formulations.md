# models.propellants.formulations

Ready-to-use propellant formulation instances loaded from bundled JSON files.

**Solid formulations** (in `formulations.solid`):
`KNDX`, `KNSB`, `KNSB_NAKKA`, `KNSU`, `KNER`, `RNX_57`, `RNX_71V`, `MIT_CHERRY_LIMEADE`

**Biliquid formulations** (in `formulations.biliquid`):
`LOX_LH2_6_0`

You can also load custom formulations from JSON with `get_propellant_from_json(filepath)`. The JSON schema expects `mixture_type`, `components` (with chemical formula, density, enthalpy, role, and optionally mass fractions), `properties`, and `burn_rate_map` (for solids).

::: machwave.models.propellants.formulations
