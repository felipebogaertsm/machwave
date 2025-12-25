import numpy as np

from machwave.common.decorators import timing
from machwave.models.propulsion.propellants import categories as propellant_categories
from machwave.models.propulsion.propellants import components as propellant_components


@timing
def main() -> None:
    lox = propellant_components.PropellantComponent(
        name="LOX",
        role=propellant_components.ComponentRole.OXIDIZER,
        density=1141.0,
        chemical_formula={"O": 2},
        enthalpy=-118730.0,
    )
    lh2 = propellant_components.PropellantComponent(
        name="LH2",
        role=propellant_components.ComponentRole.FUEL,
        density=70.8,
        chemical_formula={"H": 2},
        enthalpy=0.0,
    )

    loxlh2 = propellant_categories.BiliquidPropellant(
        name="LOX/LH2",
        components=[lox, lh2],
        combustion_efficiency=0.99,
        of_ratio=6.0,
    )

    chamber_pressure_range = np.linspace(1e5, 10e6, 100)
    loxlh2_properties = [loxlh2.evaluate(cp) for cp in chamber_pressure_range]

    print("Frozen Specific Impulse and Adiabatic Flame Temperature for LOX/LH2:")
    for cp, props in zip(chamber_pressure_range, loxlh2_properties):
        print(
            f"{cp / 1e6:.2f} MPa | {props.i_sp_frozen:.2f} s | {props.adiabatic_flame_temperature:.2f} K"
        )


if __name__ == "__main__":
    main()
