"""
Example of a RocketPy 6DOF simulation of a `machwave` solid motor using the
`RocketPySolidMotorAdapter`.

This example demonstrates how to:
1. Create and simulate a solid rocket motor using machwave
2. Adapt the motor state to RocketPy's interface
3. Run a complete 6DOF flight simulation using RocketPy
"""

from machwave.adapters.rocketpy import RocketPySolidMotorAdapter
from machwave.common import decorators
from machwave.models.propulsion import grain as grain_models
from machwave.models.propulsion import motors
from machwave.models.propulsion import thrust_chamber as thrust_chamber_models
from machwave.models.propulsion.grain import geometries as grain_geometries
from machwave.models.propulsion.propellants.formulations import (
    solid as solid_propellants,
)
from machwave.simulations import internal_ballistics
from rocketpy import Environment, Flight, Rocket


@decorators.timing
def main():
    # ============================================================================
    # 1. MOTOR SETUP
    # ============================================================================
    propellant = solid_propellants.KNSB_NAKKA

    grain = grain_models.Grain(spacing=0.01)
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=0.085,
        core_diameter=0.035,
        length=0.150,
    )
    for _ in range(4):
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
        dry_mass=6.0,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.35, 0.0, 0.0),
    )

    motor = motors.SolidMotor(
        grain=grain,
        propellant=propellant,
        thrust_chamber=thrust_chamber,
    )

    # ============================================================================
    # 2. RUN MACHWAVE INTERNAL BALLISTICS SIMULATION
    # ============================================================================
    params = internal_ballistics.InternalBallisticsParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1.013e5,
    )

    simulation = internal_ballistics.InternalBallistics(motor=motor, params=params)
    time, motor_state = simulation.run()

    simulation.print_results()

    # ============================================================================
    # 3. CREATE ROCKETPY ADAPTER
    # ============================================================================
    rocketpy_motor = RocketPySolidMotorAdapter(motor_state)
    print(f"  - Total impulse: {rocketpy_motor.total_impulse:.1f} N·s")
    print(f"  - Average thrust: {rocketpy_motor.average_thrust:.1f} N")
    print(f"  - Max thrust: {rocketpy_motor.max_thrust:.1f} N")
    print(f"  - Burn time: {rocketpy_motor.burn_time[1]:.2f} s")

    # ============================================================================
    # 4. SETUP ROCKETPY ROCKET
    # ============================================================================
    rocket = Rocket(
        radius=0.0508,  # 101.6mm outer diameter / 2
        mass=15.0,  # Dry mass without motor (kg)
        inertia=(6.0, 6.0, 0.035),  # Inertia tensor (I_11, I_22, I_33) in kg·m²
        power_off_drag=0.5,  # Drag coefficient when motor is off
        power_on_drag=0.5,  # Drag coefficient when motor is on
        center_of_mass_without_motor=0.0,  # Center of mass without motor
    )

    rocket.add_motor(rocketpy_motor, position=-0.6)  # Motor position relative to nose

    rocket.set_rail_buttons(
        upper_button_position=0.082,
        lower_button_position=-0.618,
        angular_position=45,
    )

    _ = rocket.add_nose(
        length=0.55,
        kind="vonKarman",
        position=1.16,
    )

    _ = rocket.add_trapezoidal_fins(
        n=4,
        root_chord=0.12,
        tip_chord=0.06,
        span=0.11,
        position=-0.67,
    )

    _ = rocket.add_tail(
        top_radius=0.0508,
        bottom_radius=0.043,
        length=0.06,
        position=-0.194,
    )

    _ = rocket.add_parachute(
        name="Main",
        cd_s=1.5,  # Drag coefficient * area
        trigger=800,  # Deploy at 800m AGL
        sampling_rate=105,
        lag=1.5,
        noise=(0, 8.3, 0.5),
    )

    print(f"  - Total mass: {rocket.total_mass(0):.2f} kg")
    print(f"  - Static margin: {rocket.static_margin(0):.2f} calibers")

    # ============================================================================
    # 5. SETUP ENVIRONMENT
    # ============================================================================
    env = Environment(
        latitude=32.99,  # Spaceport America, NM
        longitude=-106.975,
        elevation=1400,
    )

    env.set_atmospheric_model(type="standard_atmosphere")
    env.set_date((2023, 6, 15, 12))  # Year, month, day, hour (UTC)

    # ============================================================================
    # 6. RUN FLIGHT SIMULATION
    # ============================================================================
    flight = Flight(
        rocket=rocket,
        environment=env,
        rail_length=5.2,  # Launch rail length in meters
        inclination=85,  # Launch angle in degrees (from vertical)
        heading=0,  # Launch azimuth in degrees
    )

    print(f"\n{'=' * 60}")
    print("FLIGHT SIMULATION RESULTS")
    print(f"{'=' * 60}")
    print(f"Apogee: {flight.apogee:.1f} m (at t={flight.apogee_time:.1f} s)")
    print(f"Max speed: {flight.max_speed:.1f} m/s (Mach {flight.max_mach_number:.2f})")
    print(f"Rail exit velocity: {flight.out_of_rail_velocity:.1f} m/s")
    print(f"Impact velocity: {abs(flight.impact_velocity):.1f} m/s")
    print(f"Total flight time: {flight.t_final:.1f} s")
    print(f"{'=' * 60}\n")

    # ============================================================================
    # 7. PLOT RESULTS
    # ============================================================================
    # Flight trajectory plots
    flight.plots.trajectory_3d()


if __name__ == "__main__":
    main()
