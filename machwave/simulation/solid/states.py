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
import machwave.simulation.states as simulation_states
from machwave.simulation.solid.results import SolidSimulationResult


class SolidMotorState(simulation_states.MotorState):
    """State for a Solid Rocket Motor."""

    result_class = SolidSimulationResult

    def __init__(
        self,
        motor: motors.SolidMotor,
        igniter_pressure: float,
        external_pressure: float,
        other_losses: float,
    ) -> None:
        super().__init__(
            motor=motor,
            igniter_pressure=igniter_pressure,
            external_pressure=external_pressure,
            other_losses=other_losses,
        )

        self.motor: motors.SolidMotor = motor

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
        """Iterate the motor operation by calculating operational parameters.

        Args:
            d_t: Time increment [s].
            external_pressure: External pressure [Pa].
        """
        if self.end_thrust:
            return

        propellant_properties = self.motor.propellant.properties
        if propellant_properties is None:
            raise ValueError(
                "Propellant properties must be defined to run the simulation."
            )

        nozzle = self.motor.thrust_chamber.nozzle
        ideal_density = self.motor.propellant.ideal_density

        self.time.append(self.time[-1] + d_t)

        web_last = self.web[-1]
        self.burn_area.append(self.motor.grain.get_burn_area(web_last))
        self.propellant_volume.append(self.motor.grain.get_propellant_volume(web_last))
        burn_rate = self.motor.propellant.get_burn_rate(self.chamber_pressure[-1])
        self.burn_rate.append(burn_rate)
        self.web.append(web_last + burn_rate * (self.time[-1] - self.time[-2]))

        self.free_chamber_volume.append(
            self.motor.get_free_chamber_volume(self.propellant_volume[-1])
        )
        self.propellant_mass.append(
            self.motor.grain.get_propellant_mass(
                web_distance=self.web[-1],
                ideal_density=ideal_density,
            )
        )

        self.propellant_cog.append(
            self.motor.grain.get_center_of_gravity(web_distance=self.web[-1])
        )
        self.propellant_moi.append(
            self.motor.grain.get_moment_of_inertia(
                ideal_density=ideal_density,
                web_distance=self.web[-1],
            )
        )

        new_chamber_pressure = rk4.rk4th_ode_solver(
            variables={"chamber_pressure": self.chamber_pressure[-1]},
            equation=mass_balance.compute_chamber_pressure_mass_balance,
            d_t=d_t,
            external_pressure=external_pressure,
            mass_flow_in=self.get_m_dot_in(),
            free_chamber_volume=self.free_chamber_volume[-1],
            throat_area=nozzle.get_throat_area(),
            k=propellant_properties.k_chamber,
            R=propellant_properties.R_chamber,
            flame_temperature=propellant_properties.adiabatic_flame_temperature,
            discharge_coefficient=nozzle.discharge_coefficient,
        )[0]
        self.chamber_pressure.append(new_chamber_pressure)
        self.exit_pressure.append(
            isentropic.get_exit_pressure(
                propellant_properties.k_exhaust,
                nozzle.expansion_ratio,
                new_chamber_pressure,
            )
        )

        chamber_pressure_psi = conversions.convert_pa_to_psi(new_chamber_pressure)
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
            time=self.time[-1],
            c_1=nozzle.c_1,
            c_2=nozzle.c_2,
        )
        two_phase_loss = losses.get_two_phase_flow_loss_fraction(
            chamber_pressure_psi=chamber_pressure_psi,
            mass_fraction_of_condensed_phase=propellant_properties.qsi_chamber,
            expansion_ratio=nozzle.expansion_ratio,
            throat_diameter_inch=throat_diameter_inch,
            characteristic_length_inch=conversions.convert_meter_to_inch(
                self.free_chamber_volume[-1] / nozzle.get_throat_area()
            ),
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
            new_chamber_pressure,
            self.exit_pressure[-1],
            external_pressure,
            nozzle.expansion_ratio,
            propellant_properties.k_exhaust,
        )
        thrust_coefficient = nozzle_core.apply_thrust_coefficient_correction(
            ideal_thrust_coefficient, overall_efficiency
        )
        self.thrust_coefficient.append(thrust_coefficient)
        self.ideal_thrust_coefficient.append(ideal_thrust_coefficient)
        self.thrust.append(
            nozzle_core.get_thrust_from_thrust_coefficient(
                thrust_coefficient, new_chamber_pressure, nozzle.get_throat_area()
            )
        )

        if self.propellant_mass[-1] <= 0 and not self.end_burn:
            self._burn_time = self.time[-1]
            self.end_burn = True
        if not isentropic.is_flow_choked(
            new_chamber_pressure,
            external_pressure,
            isentropic.get_critical_pressure_ratio(propellant_properties.k_chamber),
        ):
            if self._burn_time is None:
                self._burn_time = self.time[-1]
            self._thrust_time = self.time[-1]
            self.end_thrust = True
