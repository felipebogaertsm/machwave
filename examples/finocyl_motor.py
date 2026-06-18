"""Solid motor with a single finocyl grain segment."""

import machwave.common.decorators as decorators
import machwave.models.grain as grain_models
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.motors as motors_models
import machwave.models.propellants.formulations as formulations
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.services.plots.internal_ballistics as internal_ballistics_plots
import machwave.simulation as simulation


@decorators.timing
def main():
    propellant = formulations.solid.KNSB_NAKKA

    grain = grain_models.Grain()
    finocyl_segment = grain_models.geometries.FinocylGrainSegment(
        length=0.300,
        outer_diameter=0.090,
        core_diameter=0.033,
        number_of_fins=4,
        fin_length=0.022,
        fin_width=0.006,
        finned_length=0.300,
    )
    grain.add_segment(finocyl_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.085,
        throat_diameter=0.034,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=0.0985,
        casing_outer_diameter=0.108,
        thermal_liner_thickness=0.003,
        internal_length=grain.total_length + 0.01,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=6.0,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.35, 0.0, 0.0),
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


if __name__ == "__main__":
    main()
