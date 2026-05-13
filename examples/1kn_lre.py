"""
Sample 1kN biliquid rocket engine, similar to HalfCat's Sphinx.
"""

from machwave import (
    feed_systems,
    motors,
    propellants,
    thrust_chamber as thrust_chamber_models,
)
from machwave.models.feed_systems import tanks
from machwave.services.plots.internal_ballistics import (
    plot_bipropellant_tank_profiles,
    thrust_pressure_plot,
)
from machwave.simulation import (
    InternalBallisticsSimulation,
    InternalBallisticsSimulationParams,
)

FUEL_NAME = "Ethanol"
OXIDIZER_NAME = "N2O"


def main():
    oxidizer = propellants.PropellantComponent(
        name=OXIDIZER_NAME,
        role=propellants.ComponentRole.OXIDIZER,
        density=745.0,
        chemical_formula={"N": 2, "O": 1},
        enthalpy=0.0,
        initial_temperature=300.0,
    )
    fuel = propellants.PropellantComponent(
        name=FUEL_NAME,
        role=propellants.ComponentRole.FUEL,
        density=789.0,
        chemical_formula={"C": 2, "H": 6, "O": 1},
        enthalpy=0.0,
        initial_temperature=300.0,
    )

    propellant = propellants.BiliquidPropellant(
        name=f"{OXIDIZER_NAME}/{FUEL_NAME}",
        components=[oxidizer, fuel],
        combustion_efficiency=0.98,
        oxidizer_to_fuel_ratio=1.9495,
    )

    fuel_tank = tanks.Tank(
        FUEL_NAME.upper(), volume=2.0e-3, temperature=300, initial_fluid_mass=1.55
    )
    oxidizer_tank = tanks.Tank(
        OXIDIZER_NAME, volume=3.80e-3, temperature=300, initial_fluid_mass=2.78
    )

    feed_system = feed_systems.StackedTankPressureFedFeedSystem(
        oxidizer_line_diameter=7.925e-3,
        oxidizer_line_length=0.5,
        fuel_line_diameter=5.715e-3,
        fuel_line_length=0.5,
        oxidizer_tank=oxidizer_tank,
        fuel_tank=fuel_tank,
        piston_loss=1e5,
    )

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=55e-3,
        throat_diameter=25.4e-3,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=4,
    )

    injector = thrust_chamber_models.BipropellantInjector(
        discharge_coefficient_fuel=0.48,
        discharge_coefficient_oxidizer=0.48,
        area_fuel=8.2e-6 / 0.48,
        area_ox=1.4e-5 / 0.48,
    )

    chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=70e-3,
        casing_outer_diameter=76e-3,
        internal_length=13e-3,
        thermal_liner_thickness=2e-3,
    )
    thrust_chamber = thrust_chamber_models.LiquidEngineThrustChamber(
        nozzle=nozzle,
        injector=injector,
        combustion_chamber=chamber,
        dry_mass=2,
        center_of_gravity_coordinate=(0.02, 0.0, 0.0),
    )

    lre = motors.LiquidEngine(
        propellant=propellant,
        feed_system=feed_system,
        thrust_chamber=thrust_chamber,
        oxidizer_tank_cog=0.5,
        fuel_tank_cog=0.4,
    )

    sim_params = InternalBallisticsSimulationParams(
        d_t=1e-4, igniter_pressure=1e6, external_pressure=1e5, other_losses=0.12
    )
    simulation = InternalBallisticsSimulation(motor=lre, params=sim_params)

    result = simulation.run()

    result.report()
    thrust_pressure_plot(result.time, result.thrust, result.chamber_pressure).show()
    plot_bipropellant_tank_profiles(
        result.time,
        result.oxidizer_tank_pressure,
        result.fuel_tank_pressure,
        result.oxidizer_mass,
        result.fuel_mass,
    ).show()


if __name__ == "__main__":
    main()
