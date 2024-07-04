"""
This example demonstrates the capability of analyzing different grain 
geometries within RocketSolver.
"""

import os
import sys

import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from rocketsolver.models.propulsion.grain.geometries import (
    BatesSegment,
    MultiPortGrainSegment,
    ConicalGrainSegment,
)

np.set_printoptions(precision=2, suppress=True)


def main():
    bates_segment = BatesSegment(
        length=68e-3,
        outer_diameter=41e-3,
        core_diameter=15e-3,
        spacing=0.01,
    )

    multiport_segment = MultiPortGrainSegment(
        length=68e-3,
        outer_diameter=41e-3,
        spacing=0.01,
        port_diameter=3e-3,
        port_radial_count=6,
        port_level_count=4,
    )

    conical_segment = ConicalGrainSegment(
        length=68e-3,
        outer_diameter=41e-3,
        upper_core_diameter=15e-3,
        lower_core_diameter=15e-3,
        spacing=0.01,
    )

    web_distance = 0

    grain_area = bates_segment.get_burn_area(web_distance=web_distance)
    port_area = bates_segment.get_port_area(web_distance=web_distance)
    print(f"BATES grain area: {grain_area * 1e6:2f} mm^2")
    print(f"BATES grain port area: {port_area * 1e6:2f} mm^2")

    grain_area = multiport_segment.get_burn_area(web_distance=web_distance)
    port_area = multiport_segment.get_port_area(web_distance=web_distance)
    print(f"Multiport grain area: {grain_area * 1e6:2f} mm^2")
    print(f"Multiport grain port area: {port_area * 1e6:2f} mm^2")

    grain_area = conical_segment.get_burn_area(web_distance=web_distance)
    print(f"Conical grain area: {grain_area * 1e6:2f} mm^2")
    port_area = conical_segment.get_port_area(web_distance=web_distance)
    print(f"Conical grain port area: {port_area * 1e6:2f} mm^2")


if __name__ == "__main__":
    main()
