"""
Sample 1kN biliquid rocket engine, similar to HalfCat's Sphinx.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models import materials
from machwave.models.propulsion import feed_systems, motors, propellants
from machwave.models.propulsion import thrust_chamber as thrust_chamber_models
from machwave.models.propulsion.feed_systems import tanks
from machwave.services.plots.internal_ballistics import (
    plot_bipropellant_tank_profiles,
    thrust_pressure_plot,
)
from machwave.simulations.internal_ballistics import (
    InternalBallistics,
    InternalBallisticsParams,
)

FUEL_NAME = "Ethanol"
OXIDIZER_NAME = "N2O"


def main():
    propellant = propellants.BiliquidPropellant(
        oxidizer_name=OXIDIZER_NAME, fuel_name=FUEL_NAME, of_ratio=1.9495
    )

    fuel_tank = tanks.Tank(
        FUEL_NAME.upper(), volume=2.261e-4, temperature=300, initial_fluid_mass=1.55
    )
    oxidizer_tank = tanks.Tank(
        OXIDIZER_NAME, volume=3.622e-3, temperature=300, initial_fluid_mass=2.78
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
        material=materials.Steel(),
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
        nozzle=nozzle, injector=injector, combustion_chamber=chamber, dry_mass=2
    )

    lre = motors.LiquidEngine(
        propellant=propellant, feed_system=feed_system, thrust_chamber=thrust_chamber
    )

    sim_params = InternalBallisticsParams(
        d_t=1e-3, igniter_pressure=1e6, external_pressure=1e5
    )
    simulation = InternalBallistics(motor=lre, params=sim_params)

    (time, ib_state) = simulation.run()

    simulation.print_results()
    thrust_pressure_plot(time, ib_state.thrust, ib_state.P_0).show()
    plot_bipropellant_tank_profiles(
        time,
        ib_state.oxidizer_tank_pressure,
        ib_state.fuel_tank_pressure,
        ib_state.oxidizer_mass,
        ib_state.fuel_mass,
    ).show()


if __name__ == "__main__":
    main()
