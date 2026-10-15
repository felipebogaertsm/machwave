"""
This example simulates a rocket with the Nero motor, developed at
Supernova Rocketry UFJF in 2019. It is a class J KNDX motor with a
maximum operating pressure of 7 MPa.
"""

import time

import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants.formulations as formulations
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.services.plots.internal_ballistics as internal_ballistics_plots
import machwave.simulation as simulation


def main():
    propellant = formulations.solid.KNDX

    grain = grain_models.Grain(spacing=10e-3)
    bates_segment = grain_models.geometries.BatesSegment(
        outer_diameter=41e-3,
        core_diameter=15e-3,
        length=67.5e-3,
    )

    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)
    grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        throat_diameter=9.5e-3,
        divergent_angle=12,
        expansion_ratio=8,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        inner_diameter=42.5e-3,
        internal_length=grain.total_length + 10e-3,
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
    start_time = time.perf_counter()
    main()
    print(f"\nExecution time: {time.perf_counter() - start_time:.4f} seconds")
