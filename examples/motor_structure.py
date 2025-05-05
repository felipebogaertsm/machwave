import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.models.materials import EPDM, Al6063T5, Steel
from machwave.models.propulsion.thermals import ThermalLiner
from machwave.models.propulsion.thrust_chamber.combustion_chamber import (
    BoltedCombustionChamber,
)
from machwave.services.decorators import timing

MEOP = 5.1e6  # Pa


@timing
def main():
    liner = ThermalLiner(thickness=0.003, material=EPDM())
    chamber = BoltedCombustionChamber(
        inner_diameter=0.1282,
        outer_diameter=0.1413,
        liner=liner,
        length=1,
        casing_material=Al6063T5(),
        bulkhead_material=Al6063T5(),
        screw_material=Steel(),
        max_screw_count=30,
        screw_clearance_diameter=0.0085,
        screw_diameter=0.00675,
    )

    casing_safety_factor = chamber.get_casing_safety_factor(chamber_pressure=MEOP)
    print(f"Casing safety factor: {casing_safety_factor:.2f}")

    total_axial_load = chamber._total_axial_load(chamber_pressure=MEOP)
    print(f"Total axial load: {total_axial_load:.2f} N")

    ideal_screw_count = chamber.get_optimal_fasteners(chamber_pressure=MEOP)
    print(f"Ideal screw count: {ideal_screw_count[0]} screws")
    print(f"Safety factor: {ideal_screw_count[1]:.2f}")
    print(ideal_screw_count)


if __name__ == "__main__":
    main()
