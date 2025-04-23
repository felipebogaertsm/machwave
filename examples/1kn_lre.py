"""
Sample 1kN biliquid rocket engine, similar to HalfCat's Sphinx.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models.propulsion.motors import LiquidEngine
from machwave.models.propulsion.propellants import BiliquidPropellant
from machwave.models.propulsion.feed_systems import StackedTankPressureFedFeedSystem
from machwave.models.propulsion.feed_systems.tanks import Tank
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.models.propulsion.thrust_chamber import LiquidEngineThrustChamber
from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
    CombustionChamber,
)
from machwave.models.propulsion.thrust_chamber.nozzle import Nozzle
from machwave.models.propulsion.thrust_chamber.injector import BipropellantInjector
from machwave.models.materials.metals import Steel, Al6061T6
from machwave.models.materials.polymers import EPDM
from machwave.simulations.internal_ballistics import (
    InternalBallistics,
    InternalBallisticsParams,
)
from machwave.services.plots.internal_ballistics import (
    thrust_pressure_plot,
    plot_bipropellant_tank_profiles,
)

FUEL_NAME = "Ethanol"
OXIDIZER_NAME = "N2O"


def main():
    propellant = BiliquidPropellant(
        oxidizer_name=OXIDIZER_NAME, fuel_name=FUEL_NAME, of_ratio=1.9495
    )

    fuel_tank = Tank(
        FUEL_NAME.upper(), volume=2.261e-4, temperature=300, initial_fluid_mass=1.55
    )
    oxidizer_tank = Tank(
        OXIDIZER_NAME, volume=3.622e-3, temperature=300, initial_fluid_mass=2.78
    )

    feed_system = StackedTankPressureFedFeedSystem(
        oxidizer_line_diameter=7.925e-3,
        oxidizer_line_length=0.5,
        fuel_line_diameter=5.715e-3,
        fuel_line_length=0.5,
        oxidizer_tank=oxidizer_tank,
        fuel_tank=fuel_tank,
    )

    nozzle = Nozzle(
        inlet_diameter=55e-3,
        throat_diameter=25.4e-3,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=4,
        material=Steel(),
    )

    injector = BipropellantInjector(
        discharge_coefficient_fuel=0.48,
        discharge_coefficient_oxidizer=0.48,
        area_fuel=8.2e-6 / 0.48,
        area_ox=1.4e-5 / 0.48,
    )

    liner = ThermalLiner(thickness=0.003, material=EPDM())
    chamber = CombustionChamber(
        inner_diameter=70e-3,
        outer_diameter=76e-3,
        liner=liner,
        length=25e-2,
        casing_material=Al6061T6(),
        bulkhead_material=Al6061T6(),
    )
    thrust_chamber = LiquidEngineThrustChamber(
        nozzle=nozzle, injector=injector, combustion_chamber=chamber, dry_mass=2
    )

    lre = LiquidEngine(
        propellant=propellant, feed_system=feed_system, thrust_chamber=thrust_chamber
    )

    sim_params = InternalBallisticsParams(
        d_t=1e-3, igniter_pressure=1e6, external_pressure=1e5
    )
    simulation = InternalBallistics(motor=lre, params=sim_params)

    (time, ib_operation) = simulation.run()

    simulation.print_results()
    thrust_pressure_plot(time, ib_operation.thrust, ib_operation.P_0).show()
    plot_bipropellant_tank_profiles(
        time,
        ib_operation.oxidizer_tank_pressure,
        ib_operation.fuel_tank_pressure,
        ib_operation.oxidizer_mass,
        ib_operation.fuel_mass,
    ).show()


if __name__ == "__main__":
    main()
