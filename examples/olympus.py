"""
Olympus is an O-class solid rocket motor designed during the LASC Costate
Program (2020-2022). It was originally intended for a 5km-apogee rocket but
never used in flight. The motor was successfully tested on July 2, 2022, and
at the time, it was the largest experimental motor ever built in Latin America.
"""

import machwave.common.decorators as decorators
import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.propellants.formulations as formulations
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.services.plots.internal_ballistics as internal_ballistics_plots
import machwave.simulation as simulation


@decorators.timing
def main():
    propellant = formulations.solid.KNSB_NAKKA

    grain = grain_models.Grain()
    bates_segment_45 = grain_models.geometries.BatesSegment(
        outer_diameter=0.116,
        core_diameter=0.045,
        length=0.200,
    )
    bates_segment_60 = grain_models.geometries.BatesSegment(
        outer_diameter=0.116,
        core_diameter=0.060,
        length=0.200,
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
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
    )

    motor = motors_models.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
        combustion_efficiency=0.95,
    )

    params = simulation.InternalBallisticsSimulationParams(
        d_t=0.001,
        igniter_pressure=1e6,
        external_pressure=1.013e5,
    )

    sim = simulation.InternalBallisticsSimulation(motor=motor, params=params)
    result = sim.run()

    result.report()

    internal_ballistics_plots.thrust_pressure_plot(
        result.time, result.thrust, result.chamber_pressure
    ).show()
    internal_ballistics_plots.thrust_coefficient_plot(
        result.time,
        result.ideal_thrust_coefficient,
        result.thrust_coefficient,
        show_efficiency=True,
    ).show()


if __name__ == "__main__":
    main()
