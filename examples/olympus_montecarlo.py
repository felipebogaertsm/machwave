import machwave.common.decorators as decorators
import machwave.models.grain as grain_models
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.motors as motors_models
import machwave.models.propellants.formulations as formulations
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.montecarlo as montecarlo
import machwave.simulation as simulation

MC_SAMPLES = 1000


@decorators.timing
def main():
    propellant = formulations.solid.KNSB_NAKKA

    grain = grain_models.Grain(
        spacing=montecarlo.MonteCarloParameter(0.010, spread=0.005),
    )
    for _ in range(4):
        grain.add_segment(
            grain_models.geometries.BatesSegment(
                outer_diameter=montecarlo.MonteCarloParameter(0.115, spread=0.002),
                core_diameter=montecarlo.MonteCarloParameter(0.045, spread=0.002),
                length=montecarlo.MonteCarloParameter(0.200, spread=0.005),
            )
        )
    for _ in range(3):
        grain.add_segment(
            grain_models.geometries.BatesSegment(
                outer_diameter=montecarlo.MonteCarloParameter(0.115, spread=0.002),
                core_diameter=montecarlo.MonteCarloParameter(0.060, spread=0.002),
                length=montecarlo.MonteCarloParameter(0.200, spread=0.005),
            )
        )

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.080,
        throat_diameter=0.037,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
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
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.5, 0.0, 0.0),
    )

    motor = motors_models.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
        combustion_efficiency=0.95,
        nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model(
            other_losses=0.12
        ),
    )

    ib_params = simulation.InternalBallisticsSimulationParams(
        d_t=0.01,
        external_pressure=1e5,
        igniter_pressure=1e6,
    )

    mc = montecarlo.MonteCarloSimulation(
        [motor, ib_params],
        MC_SAMPLES,
        simulation.InternalBallisticsSimulation,
    )
    mc.run()

    total_impulse_stats = mc.get_property_stats("total_impulse")
    print(f"Total impulse (N.s) mean: {total_impulse_stats.get('mean'):.2f}")
    print(f"Total impulse (N.s) median: {total_impulse_stats.get('median'):.2f}")
    print(f"Total impulse (N.s) variance: {total_impulse_stats.get('variance'):.2f}")
    print(f"Total impulse (N.s) std: {total_impulse_stats.get('std_dev'):.2f}")

    mc.plot_histogram("total_impulse", "Total Impulse (N·s)")
    mc.plot_histogram_with_kde("total_impulse", "Total Impulse (N·s)")
    mc.plot_cdf("total_impulse", "Total Impulse (N·s)")
    mc.plot_time_series_extremes(
        time_property="time",
        series_property="chamber_pressure",
        title="Pressão de Câmara (MPa)",
    )
    mc.plot_time_series_extremes(
        time_property="time",
        series_property="thrust",
        title="Força de Empuxo (N)",
    )


if __name__ == "__main__":
    main()
