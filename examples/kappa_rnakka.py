"""
Example for the Kappa motor, developed by Richard Nakka.
https://www.nakka-rocketry.net/kappa.html
"""

import machwave.common.decorators as decorators
import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants.formulations as formulations
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.services.plots.internal_ballistics as internal_ballistics_plots
import machwave.simulation as simulation


@decorators.timing
def main():
    propellant = formulations.solid.KNDX

    grain = grain_models.Grain(spacing=5e-3)
    bates_segment = grain_models.geometries.BatesSegment(
        outer_diameter=55e-3,
        core_diameter=19e-3,
        length=101.6e-3,
    )

    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=40e-3,
        throat_diameter=12.8e-3,
        divergent_angle=12,
        convergent_angle=25,
        expansion_ratio=11,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=60e-3,
        casing_outer_diameter=64e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 5e-3,
    )

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=0.85,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.035, 0.0, 0.0),
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
        external_pressure=1e5,
    )

    sim = simulation.InternalBallisticsSimulation(motor=motor, params=params)
    result = sim.run()

    internal_ballistics_plots.thrust_pressure_plot(
        result.time, result.thrust, result.chamber_pressure
    ).show()

    result.report()


if __name__ == "__main__":
    main()
