"""
This example simulates a rocket with an APCP solid motor, using
an InternalBallisticsCoupled simulation that includes both
internal ballistics and atmospheric flight.
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
    propellant = formulations.solid.MIT_CHERRY_LIMEADE

    grain = grain_models.Grain(spacing=0.01)
    bates_segment = grain_models.geometries.BatesSegment(
        outer_diameter=0.085,
        core_diameter=0.035,
        length=0.150,
    )

    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.080,
        throat_diameter=0.022,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=95.25e-3,
        casing_outer_diameter=101.6e-3,
        thermal_liner_thickness=3e-3,
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
        nozzle_loss_model=nozzle_losses.presets.spp1975_solid_loss_model(
            other_losses=0.12
        ),
    )

    params = simulation.InternalBallisticsSimulationParams(
        d_t=0.01,
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
