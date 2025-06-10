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
                outer_diameter=montecarlo.MonteCarloParameter(0.117, tolerance=0.002),
                core_diameter=montecarlo.MonteCarloParameter(0.045, tolerance=0.002),
                length=montecarlo.MonteCarloParameter(0.195, tolerance=0.005),
                spacing=montecarlo.MonteCarloParameter(0.010, tolerance=0.005),
            )
        )
    for _ in range(3):
        grain.add_segment(
            grain_geometries.BatesSegment(
                outer_diameter=montecarlo.MonteCarloParameter(0.117, tolerance=0.002),
                core_diameter=montecarlo.MonteCarloParameter(0.060, tolerance=0.002),
                length=montecarlo.MonteCarloParameter(0.195, tolerance=0.005),
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
        10_000,
        internal_ballistics.InternalBallistics,
    )
    mc.run()

    total_impulse_stats = mc.get_property_stats(1, "total_impulse")
    print(f"Total impulse (N.s) mean: {total_impulse_stats.get('mean'):.2f}")
    print(f"Total impulse (N.s) median: {total_impulse_stats.get('median'):.2f}")
    print(f"Total impulse (N.s) variance: {total_impulse_stats.get('variance'):.2f}")
    print(f"Total impulse (N.s) std: {total_impulse_stats.get('std_dev'):.2f}")

    mc.plot_histogram(1, "total_impulse", "Total Impulse (N·s)")
    mc.plot_histogram_with_kde(1, "total_impulse", "Total Impulse (N·s)")
    mc.plot_cdf(1, "total_impulse", "Total Impulse (N·s)")
    mc.plot_time_series_extremes(
        1,
        "t",
        series_property="P_0",
        title="Thrust Time Series",
    )


if __name__ == "__main__":
    main()
