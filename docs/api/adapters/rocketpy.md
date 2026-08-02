# RocketPy Integration

Machwave can drive RocketPy flight simulations by adapting a Machwave motor and
its simulation result into a RocketPy-compatible motor object. The integration
is intended for workflows where Machwave computes the internal ballistics and
RocketPy handles the 6-DOF trajectory, aerodynamics, and recovery simulation.

## Installation

Install the optional RocketPy dependency:

```bash
pip install machwave[rocketpy]
```

## Integration Workflow

The adapter sits after the internal ballistics simulation:

1. Build a Machwave motor model.
2. Run `InternalBallisticsSimulation` to obtain a `SimulationResult`.
3. Wrap the motor and result with `RocketPySolidMotorAdapter(motor=motor, simulation_result=result)`.
4. Pass the adapted motor into a RocketPy `Rocket`.

## Example

```python
from machwave import (
    formulations,
    grain as grain_models,
    motors,
    simulation,
    thrust_chamber as thrust_chamber_models,
)
from machwave.adapters.rocketpy import RocketPySolidMotorAdapter
from machwave.common.mass_properties import DryMassProperties
from rocketpy import Environment, Flight, Rocket

propellant = formulations.solid.KNSB_NAKKA

grain = grain_models.Grain(spacing=0.01)
segment = grain_models.geometries.BatesSegment(
	outer_diameter=0.085,
	core_diameter=0.035,
	length=0.150,
)
for _ in range(4):
	grain.add_segment(segment)

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

# Trajectory simulations require the dry mass properties
thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
	nozzle=nozzle,
	combustion_chamber=combustion_chamber,
	nozzle_exit_to_grain_port_distance=0.01,
	dry_mass_properties=DryMassProperties(
		dry_mass=6.0,
		center_of_gravity_coordinate=(0.35, 0.0, 0.0),
		moment_of_inertia=(0.19, 0.19, 0.008),
	),
)

motor = motors.SolidMotor(
	grain=grain,
	propellant=propellant,
	thrust_chamber=thrust_chamber,
)

params = simulation.InternalBallisticsSimulationParams(
	d_t=0.01,
	igniter_pressure=1e6,
	external_pressure=1.013e5,
)

result = simulation.InternalBallisticsSimulation(
	motor=motor,
	params=params,
).run()

rocketpy_motor = RocketPySolidMotorAdapter(motor=motor, simulation_result=result)

rocket = Rocket(
	radius=0.0508,
	mass=15.0,
	inertia=(6.0, 6.0, 0.035),
	power_off_drag=0.5,
	power_on_drag=0.5,
	center_of_mass_without_motor=0.0,
)
rocket.add_motor(rocketpy_motor, position=-0.6)

env = Environment(latitude=32.99, longitude=-106.975, elevation=1400)
env.set_atmospheric_model(type="standard_atmosphere")

flight = Flight(
	rocket=rocket,
	environment=env,
	rail_length=5.2,
	inclination=85,
	heading=0,
)
```

For a full runnable script, see `examples/rocketpy_srm_simulation.py`.

## Data Passed To RocketPy

`RocketPyMotorAdapter` builds the RocketPy motor inputs from the Machwave motor
and its simulation result. The adapter currently provides:

- thrust curve from Machwave time history
- burn-time interval
- dry mass, dry-mass center of gravity, and dry-mass moments of inertia
- nozzle radius and throat radius
- propellant initial mass
- propellant center of mass over time
- propellant inertia tensor components over time
- reference pressure from the exit-pressure trace

## Current Scope And Limitations

- `RocketPySolidMotorAdapter` is the currently implemented adapter.
- RocketPy must be installed, otherwise adapter import or initialization raises `ImportError`.
- The solid-motor adapter assumes RocketPy's segmented-grain model and uses the first Machwave grain segment as the representative geometry.
- The thrust chamber must define `dry_mass_properties`; the adapter raises `ValueError` otherwise.
- The coordinate system orientation is `nozzle_to_combustion_chamber`, and `nozzle_position` is zero, so RocketPy measures from the nozzle exit. Machwave's motor frame shares that origin, so the propellant and dry mass positions pass through unchanged.

## API Reference

::: machwave.adapters.rocketpy
