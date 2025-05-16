import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave import montecarlo
from machwave.common.decorators import timing
from machwave.models import materials
from machwave.models.propulsion import grain as grain_models
from machwave.models.propulsion import motors
from machwave.models.propulsion import thrust_chamber as thrust_chamber_models
from machwave.models.propulsion.grain import geometries as grain_geometries
from machwave.models.propulsion.propellants import solid as solid_propellants
from machwave.simulations import internal_ballistics


@timing
def main():
    propellant = solid_propellants.KNSB_NAKKA

    grain = grain_models.Grain()
    for _ in range(4):
        grain.add_segment(
            grain_geometries.BatesSegment(
                outer_diameter=montecarlo.MonteCarloParameter(0.115, tolerance=0.001),
                core_diameter=montecarlo.MonteCarloParameter(0.045, tolerance=0.001),
                length=montecarlo.MonteCarloParameter(0.200, tolerance=0.001),
                spacing=montecarlo.MonteCarloParameter(0.010, tolerance=0.005),
            )
        )
    for _ in range(3):
        grain.add_segment(
            grain_geometries.BatesSegment(
                outer_diameter=montecarlo.MonteCarloParameter(0.115, tolerance=0.001),
                core_diameter=montecarlo.MonteCarloParameter(0.060, tolerance=0.001),
                length=montecarlo.MonteCarloParameter(0.200, tolerance=0.001),
                spacing=montecarlo.MonteCarloParameter(0.010, tolerance=0.005),
            )
        )

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.080,
        throat_diameter=montecarlo.MonteCarloParameter(0.037, tolerance=0.0005),
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=materials.Steel(),
    )

    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=0.1282,
        casing_outer_diameter=0.1413,
        thermal_liner_thickness=0.003,
        internal_length=grain.total_length + 0.010,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=21.013,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
    )

    motor = motors.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    ib_params = internal_ballistics.InternalBallisticsParams(
        d_t=0.01,
        external_pressure=1e5,
        igniter_pressure=1e6,
    )

    mc = montecarlo.MonteCarloSimulation(
        [motor, ib_params],
        100,
        internal_ballistics.InternalBallistics,
    )
    mc.run()
    mc.plot_histogram(1, "total_impulse", "Total Impulse (N·s)")
    mc.plot_histogram(1, "specific_impulse", "Specific Impulse (N·s)")


if __name__ == "__main__":
    main()
