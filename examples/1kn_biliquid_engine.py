"""
Sample 1kN biliquid rocket engine, similar to HalfCat's Sphinx.
"""

import machwave.models.feed_systems as feed_systems
import machwave.models.feed_systems.tank as tank
import machwave.models.motors as motors_models
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants as propellants
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.services.plots.internal_ballistics as internal_ballistics_plots
import machwave.simulation as simulation_module

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
        oxidizer_to_fuel_ratio=1.9495,
    )

    fuel_tank = tank.Tank(
        FUEL_NAME.upper(), volume=2.0e-3, temperature=300, initial_fluid_mass=1.55
    )
    oxidizer_tank = tank.Tank(
        OXIDIZER_NAME, volume=3.80e-3, temperature=300, initial_fluid_mass=2.78
    )

    feed_system = feed_systems.StackedTankPressureFedFeedSystem.from_oxidizer_and_fuel(
        oxidizer_tank=oxidizer_tank,
        fuel_tank=fuel_tank,
        piston_loss=1e5,
        oxidizer_line_loss=2e5,
        fuel_line_loss=2e5,
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
    thrust_chamber = thrust_chamber_models.BiliquidEngineThrustChamber(
        nozzle=nozzle,
        injector=injector,
        combustion_chamber=chamber,
    )

    engine = motors_models.BiliquidEngine(
        propellant=propellant,
        feed_system=feed_system,
        thrust_chamber=thrust_chamber,
        combustion_efficiency=0.98,
        nozzle_loss_model=nozzle_losses.presets.constant_efficiency_loss_model(
            efficiency=0.88, mixture_type=propellants.MixtureType.BILIQUID
        ),
    )

    sim_params = simulation_module.InternalBallisticsSimulationParams(
        d_t=1e-4, igniter_pressure=1e6, external_pressure=1e5
    )
    simulation = simulation_module.InternalBallisticsSimulation(
        motor=engine, params=sim_params
    )

    result = simulation.run()

    result.report()
    internal_ballistics_plots.thrust_pressure_plot(
        result.time, result.thrust, result.chamber_pressure
    ).show()
    internal_ballistics_plots.plot_bipropellant_tank_profiles(
        result.time,
        result.oxidizer_tank_pressure,
        result.fuel_tank_pressure,
        result.oxidizer_mass,
        result.fuel_mass,
    ).show()


if __name__ == "__main__":
    main()
