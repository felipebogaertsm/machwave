import numpy as np

from machwave.common.decorators import timing
from machwave.models.propulsion.propellants import categories as propellant_categories
from machwave.models.propulsion.propellants import components as propellant_components


@timing
def main() -> None:
    potassium_nitrate = propellant_components.PropellantComponent(
        name="Potassium Nitrate",
        mass_fraction=0.65,
        role=propellant_components.ComponentRole.OXIDIZER,
        density=2100.0,
        chemical_formula={"K": 1, "N": 1, "O": 3},
        enthalpy=-494600.0,
    )
    sucrose = propellant_components.PropellantComponent(
        name="Sucrose",
        mass_fraction=0.35,
        role=propellant_components.ComponentRole.FUEL,
        density=1590.0,
        chemical_formula={"C": 12, "H": 22, "O": 11},
        enthalpy=-2226100.0,
    )

    knsu = propellant_categories.SolidPropellant(
        name="KNSU",
        components=[potassium_nitrate, sucrose],
        combustion_efficiency=0.95,
        burn_rate=[{"min": 0, "max": 100000000, "a": 8.260, "n": 0.319}],
    )

    chamber_pressure_range = np.linspace(1e5, 10e6, 100)
    knsu_properties = [knsu.evaluate(cp) for cp in chamber_pressure_range]

    print("Frozen Specific Impulse and Adiabatic Flame Temperature for KNSU:")
    for cp, props in zip(chamber_pressure_range, knsu_properties):
        print(
            f"{cp / 1e6:.2f} MPa | {props.i_sp_frozen:.2f} s | {props.adiabatic_flame_temperature:.2f} K"
        )


if __name__ == "__main__":
    main()
