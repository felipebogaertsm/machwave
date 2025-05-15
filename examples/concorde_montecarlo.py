import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from machwave.services.decorators import timing
from machwave.models import materials
from machwave.models import atmosphere
from machwave.models.propulsion import motors
from machwave.models.propulsion import grain as grain_models
from machwave.models.propulsion.grain import geometries as grain_geometries
from machwave.models.propulsion.propellants import solid as solid_propellants
from machwave.models.propulsion import thrust_chamber as thrust_chamber_models
from machwave.models import recovery as recovery_models
from machwave.models.recovery import events
from machwave.models.recovery import parachutes
from machwave.models import rocket as rocket_models
from machwave.simulations import internal_balistics_coupled
from machwave import montecarlo


@timing
def main():
    # Motor:
    propellant = solid_propellants.KNSB_NAKKA

    grain = grain_models.Grain()

    bates_segment_45 = grain_geometries.BatesSegment(
        outer_diameter=montecarlo.MonteCarloParameter(value=115e-3, tolerance=1e-3),
        core_diameter=montecarlo.MonteCarloParameter(value=45e-3, tolerance=1e-3),
        length=montecarlo.MonteCarloParameter(value=200e-3, tolerance=1e-3),
        spacing=montecarlo.MonteCarloParameter(value=10e-3, tolerance=5e-3),
    )
    bates_segment_60 = grain_geometries.BatesSegment(
        outer_diameter=montecarlo.MonteCarloParameter(value=115e-3, tolerance=1e-3),
        core_diameter=montecarlo.MonteCarloParameter(value=60e-3, tolerance=1e-3),
        length=montecarlo.MonteCarloParameter(value=200e-3, tolerance=1e-3),
        spacing=montecarlo.MonteCarloParameter(value=10e-3, tolerance=5e-3),
    )

    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_45)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)
    grain.add_segment(bates_segment_60)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=80e-3,
        throat_diameter=montecarlo.MonteCarloParameter(value=37e-3, tolerance=0.5e-3),
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
        material=materials.Steel(),
    )

    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=montecarlo.MonteCarloParameter(
            value=95.25e-3, tolerance=1e-3
        ),
        casing_outer_diameter=montecarlo.MonteCarloParameter(
            value=101.6e-3, tolerance=1e-3
        ),
        thermal_liner_thickness=3e-3,
        internal_length=grain.total_length + 0.01,
    )

    thrust_chamber = thrust_chamber_models.ThrustChamber(
        dry_mass=21.013,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
    )

    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )

    # Recovery:
    recovery = recovery_models.Recovery()
    recovery.add_event(
        events.ApogeeBasedEvent(
            trigger_value=1,
            parachute=parachutes.HemisphericalParachute(diameter=1.25),
        )
    )
    recovery.add_event(
        events.AltitudeBasedEvent(
            trigger_value=450,
            parachute=parachutes.HemisphericalParachute(diameter=2.66),
        )
    )

    # Rocket:
    fuselage = rocket_models.Fuselage(
        length=4e3,
        drag_coefficient=0.5,
        outer_diameter=0.17,
    )

    rocket = rocket_models.Rocket(
        propulsion=motor,
        recovery=recovery,
        fuselage=fuselage,
        mass_without_motor=25,
    )

    # Simulation:
    params = internal_balistics_coupled.InternalBallisticsCoupledParams(
        atmosphere.Atmosphere1976(),
        0.01,
        10,
        600,
        1.5e6,
        5,
    )

    montecarlo_sim = montecarlo.MonteCarloSimulation(
        [rocket, params],
        100,
        internal_balistics_coupled.InternalBallisticsCoupled,
    )

    montecarlo_sim.run()
    montecarlo_sim.plot_histogram(0, "total_impulse", "Total Impulse (N.s)")
    montecarlo_sim.plot_histogram(1, "apogee", "Apogee (m)")


if __name__ == "__main__":
    main()
