"""
Olympus is an O-class solid rocket motor designed during the LASC Costate
Program (2020-2022). It was originally intended for a 5km-apogee rocket but
never used in flight. The motor was successfully tested on July 2, 2022, and
at the time, it was the largest experimental motor ever built in Latin America.
"""

from machwave.common.decorators import timing
from machwave.models import grain as grain_models
from machwave.models import motors
from machwave.models import thrust_chamber as thrust_chamber_models
from machwave.models.grain import geometries as grain_geometries
from machwave.models.propellants.formulations import (
    solid as solid_propellants,
)
from machwave.services.plots import internal_ballistics as internal_ballistics_plots
from machwave import simulation


@timing
def main():
    propellant = solid_propellants.KNSB_NAKKA

    grain = grain_models.Grain()
    bates_segment_45 = grain_geometries.BatesSegment(
        outer_diameter=0.116,
        core_diameter=0.045,
        length=0.200,
        spacing=0.01,
    )
    bates_segment_60 = grain_geometries.BatesSegment(
        outer_diameter=0.116,
        core_diameter=0.060,
        length=0.200,
        spacing=0.01,
    )

    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.080,
        throat_diameter=0.037,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=9.11,
    )

    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=0.1282,
        casing_outer_diameter=0.1413,
        thermal_liner_thickness=0.003,
        internal_length=grain.total_length + 0.01,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=19.0,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.5, 0.0, 0.0),
    )

    motor = motors.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    params = simulation.InternalBallisticsParams(
        d_t=0.001,
        igniter_pressure=1e6,
        external_pressure=1.013e5,
    )

    simulation = simulation.InternalBallistics(motor=motor, params=params)
    t, ib_state = simulation.run()

    simulation.print_results()

    internal_ballistics_plots.thrust_pressure_plot(
        t, ib_state.thrust, ib_state.P_0
    ).show()
    internal_ballistics_plots.thrust_coefficient_plot(
        t, ib_state.C_f_ideal, ib_state.C_f, show_efficiency=True
    ).show()


if __name__ == "__main__":
    main()
