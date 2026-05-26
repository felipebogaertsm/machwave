from __future__ import annotations

import numpy as np
import numpy.typing as npt

import machwave.core.compressible_flow.isentropic as isentropic
import machwave.core.compressible_flow.losses as losses
import machwave.core.compressible_flow.nozzle as nozzle_core
import machwave.core.conversions as conversions
import machwave.core.mass_balance as mass_balance
import machwave.core.solvers.rk4 as rk4
import machwave.models.motors as motors
import machwave.simulation.solid.results as solid_results
import machwave.simulation.states as simulation_states


class SolidMotorState(simulation_states.MotorState):
    """State for a Solid Rocket Motor."""

    result_class = solid_results.SolidSimulationResult

    def __init__(
        self,
        motor: motors.SolidMotor,
        igniter_pressure: float,
        external_pressure: float,
        other_losses: float,
    ) -> None:
        """
        Initialize a solid motor state.

        Args:
            motor: Solid motor to track.
            igniter_pressure: Initial chamber pressure from the igniter [Pa].
            external_pressure: Ambient pressure [Pa].
            other_losses: Fractional losses not covered by specific
                mechanisms, in [0, 1].

        Raises:
            ValueError: If the motor's propellant has no thermochemical
                properties. Solid propellant properties are fixed for the
                entire run, so a missing value is a configuration error and
                the simulation refuses to start.
        """
        propellant_properties = motor.propellant.properties
        if propellant_properties is None:
            raise ValueError(
                "Propellant properties must be defined to run the simulation."
            )

        super().__init__(
            motor=motor,
            igniter_pressure=igniter_pressure,
            external_pressure=external_pressure,
            other_losses=other_losses,
        )

        self.motor: motors.SolidMotor = motor
        self.propellant_properties = propellant_properties

        self.free_chamber_volume: simulation_states.SimulationStateArray = [
            motor.thrust_chamber.combustion_chamber.internal_volume
        ]
        self.web: simulation_states.SimulationStateArray = [0.0]
        self.burn_area: simulation_states.SimulationStateArray = [
            self.motor.grain.get_burn_area(0.0)
        ]
        self.propellant_volume: simulation_states.SimulationStateArray = [
            self.motor.grain.get_propellant_volume(0.0)
        ]
        self.burn_rate: simulation_states.SimulationStateArray = [0.0]

        initial_cog = motor.grain.get_center_of_gravity(
            web_distance=0.0,
        )
        initial_moi = motor.grain.get_moment_of_inertia(
            ideal_density=motor.propellant.ideal_density,
            web_distance=0.0,
        )
        self.propellant_cog: list[npt.NDArray[np.float64]] = [initial_cog]
        self.propellant_moi: list[npt.NDArray[np.float64]] = [initial_moi]

        self.divergent_loss: simulation_states.SimulationStateArray = [0.0]
        self.kinetics_loss: simulation_states.SimulationStateArray = [0.0]
        self.boundary_layer_loss: simulation_states.SimulationStateArray = [0.0]
        self.two_phase_loss: simulation_states.SimulationStateArray = [0.0]
        self.nozzle_efficiency: simulation_states.SimulationStateArray = [0.0]
        self.overall_efficiency: simulation_states.SimulationStateArray = [0.0]

    def get_m_dot_in(self) -> float:
        """Return the propellant mass generation rate from the grain [kg/s]."""
        propellant_density = self.motor.grain.get_real_density(
            web_distance=self.web[-1],
            ideal_density=self.motor.propellant.ideal_density,
        )
        return propellant_density * self.burn_rate[-1] * self.burn_area[-1]

    def run_timestep(
        self,
        d_t: float,
        external_pressure: float,
    ) -> None:
        """
        Iterate the motor operation by calculating operational parameters.

        Args:
            d_t: Time increment [s].
            external_pressure: External pressure [Pa].
        """
        propellant_properties = self.propellant_properties
        nozzle = self.motor.thrust_chamber.nozzle
        ideal_propellant_density = self.motor.propellant.ideal_density

        time = self.time[-1] + d_t
        self.time.append(time)

        web_distance = self.web[-1]
        burn_area = self.motor.grain.get_burn_area(web_distance)
        self.burn_area.append(burn_area)
        propellant_volume = self.motor.grain.get_propellant_volume(web_distance)
        self.propellant_volume.append(propellant_volume)
        burn_rate = self.motor.propellant.get_burn_rate(self.chamber_pressure[-1])
        self.burn_rate.append(burn_rate)
        web_consumed = burn_rate * d_t
        self.web.append(web_distance + web_consumed)

        free_chamber_volume = self.motor.get_free_chamber_volume(propellant_volume)
        self.free_chamber_volume.append(free_chamber_volume)
        propellant_mass = self.motor.grain.get_propellant_mass(
            web_distance=web_distance, ideal_density=ideal_propellant_density
        )
        self.propellant_mass.append(propellant_mass)

        propellant_cog = self.motor.grain.get_center_of_gravity(
            web_distance=web_distance
        )
        self.propellant_cog.append(propellant_cog)
        propellant_moi = self.motor.grain.get_moment_of_inertia(
            ideal_density=ideal_propellant_density, web_distance=web_distance
        )
        self.propellant_moi.append(propellant_moi)

        chamber_pressure = rk4.rk4th_ode_solver(
            variables={"chamber_pressure": self.chamber_pressure[-1]},
            equation=mass_balance.compute_chamber_pressure_mass_balance,
            d_t=d_t,
            external_pressure=external_pressure,
            mass_flow_in=self.get_m_dot_in(),
            free_chamber_volume=free_chamber_volume,
            throat_area=nozzle.get_throat_area(),
            k=propellant_properties.k_chamber,
            R=propellant_properties.R_chamber,
            flame_temperature=propellant_properties.adiabatic_flame_temperature,
            nozzle_discharge_coefficient=nozzle.discharge_coefficient,
        )[0]
        self.chamber_pressure.append(chamber_pressure)
        exit_pressure = isentropic.get_exit_pressure(
            propellant_properties.k_exhaust,
            nozzle.expansion_ratio,
            chamber_pressure,
        )
        self.exit_pressure.append(exit_pressure)

        chamber_pressure_psi = conversions.convert_pa_to_psi(chamber_pressure)
        throat_diameter_inch = conversions.convert_meter_to_inch(nozzle.throat_diameter)
        divergent_loss = losses.get_nozzle_divergent_loss_fraction(
            divergent_angle=nozzle.divergent_angle,
        )
        kinetics_loss = losses.get_kinetics_loss_fraction(
            i_sp_th_frozen=propellant_properties.i_sp_frozen,
            i_sp_th_shifting=propellant_properties.i_sp_shifting,
            chamber_pressure_psi=chamber_pressure_psi,
        )
        boundary_layer_loss = losses.get_boundary_layer_loss_fraction(
            chamber_pressure_psi=chamber_pressure_psi,
            throat_diameter_inch=throat_diameter_inch,
            expansion_ratio=nozzle.expansion_ratio,
            time=time,
            c_1=nozzle.c_1,
            c_2=nozzle.c_2,
        )
        characteristic_length_inch = conversions.convert_meter_to_inch(
            free_chamber_volume / nozzle.get_throat_area()
        )
        two_phase_loss = losses.get_two_phase_flow_loss_fraction(
            chamber_pressure_psi=chamber_pressure_psi,
            mass_fraction_of_condensed_phase=propellant_properties.qsi_chamber,
            expansion_ratio=nozzle.expansion_ratio,
            throat_diameter_inch=throat_diameter_inch,
            characteristic_length_inch=characteristic_length_inch,
        )
        nozzle_efficiency = losses.get_overall_nozzle_efficiency(
            divergent_loss,
            kinetics_loss,
            boundary_layer_loss,
            two_phase_loss,
            other_losses=self.other_losses,
        )
        overall_efficiency = (
            nozzle_efficiency * self.motor.propellant.combustion_efficiency
        )
        self.divergent_loss.append(divergent_loss)
        self.kinetics_loss.append(kinetics_loss)
        self.boundary_layer_loss.append(boundary_layer_loss)
        self.two_phase_loss.append(two_phase_loss)
        self.nozzle_efficiency.append(nozzle_efficiency)
        self.overall_efficiency.append(overall_efficiency)

        ideal_thrust_coefficient = nozzle_core.get_ideal_thrust_coefficient(
            chamber_pressure,
            exit_pressure,
            external_pressure,
            nozzle.expansion_ratio,
            propellant_properties.k_exhaust,
        )
        self.ideal_thrust_coefficient.append(ideal_thrust_coefficient)
        thrust_coefficient = nozzle_core.apply_thrust_coefficient_correction(
            ideal_thrust_coefficient, overall_efficiency
        )
        self.thrust_coefficient.append(thrust_coefficient)
        thrust = nozzle_core.get_thrust_from_thrust_coefficient(
            thrust_coefficient, chamber_pressure, nozzle.get_throat_area()
        )
        self.thrust.append(thrust)

        if propellant_mass <= 0 and not self.end_burn:
            self._burn_time = time
            self.end_burn = True
        if not isentropic.is_flow_choked(
            chamber_pressure,
            external_pressure,
            isentropic.get_critical_pressure_ratio(propellant_properties.k_chamber),
        ):
            if self._burn_time is None:
                self._burn_time = time
            self._thrust_time = time
            self.end_thrust = True
