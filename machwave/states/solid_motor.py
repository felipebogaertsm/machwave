import numpy as np

import machwave.core.compressible_flow.isentropic as isentropic
import machwave.core.compressible_flow.losses as losses
import machwave.core.compressible_flow.nozzle as nozzle_core
import machwave.core.conversions as conversions
import machwave.core.mass_balance as mass_balance
import machwave.core.performance as performance
import machwave.core.solvers.rk4 as rk4
import machwave.models.motors as motors
import machwave.states.base as states_base


class SolidMotorState(states_base.MotorState):
    """
    State for a Solid Rocket Motor.
    """

    SIMULATION_ARRAY_ATTRIBUTE_NAMES = (
        states_base.MotorState.SIMULATION_ARRAY_ATTRIBUTE_NAMES
        + (
            "free_chamber_volume",
            "web",
            "burn_area",
            "propellant_volume",
            "burn_rate",
            "divergent_loss",
            "kinetics_loss",
            "boundary_layer_loss",
            "two_phase_loss",
            "nozzle_efficiency",
            "overall_efficiency",
        )
    )

    def __init__(
        self,
        motor: motors.SolidMotor,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
        other_losses: float,
    ) -> None:
        """
        Initial parameters for a SRM operation.
        """
        super().__init__(
            motor=motor,
            initial_pressure=initial_pressure,
            initial_atmospheric_pressure=initial_atmospheric_pressure,
            other_losses=other_losses,
        )

        self.motor: motors.SolidMotor = motor

        self.free_chamber_volume: states_base.SimulationArray = [
            motor.thrust_chamber.combustion_chamber.internal_volume
        ]
        self.web: states_base.SimulationArray = [0.0]
        self.burn_area: states_base.SimulationArray = [
            self.motor.grain.get_burn_area(0.0)
        ]
        self.propellant_volume: states_base.SimulationArray = [
            self.motor.grain.get_propellant_volume(0.0)
        ]
        self.burn_rate: states_base.SimulationArray = [0.0]

        initial_cog = motor.grain.get_center_of_gravity(
            web_distance=0.0,
        )
        initial_moi = motor.grain.get_moment_of_inertia(
            ideal_density=motor.propellant.ideal_density,
            web_distance=0.0,
        )
        self.propellant_cog = [initial_cog]  # [x, y, z] in meters
        self.propellant_moi = [initial_moi]  # 3x3 tensor in kg-m²

        self.divergent_loss: states_base.SimulationArray = [0.0]
        self.kinetics_loss: states_base.SimulationArray = [0.0]
        self.boundary_layer_loss: states_base.SimulationArray = [0.0]
        self.two_phase_loss: states_base.SimulationArray = [0.0]
        self.nozzle_efficiency: states_base.SimulationArray = [0.0]
        self.overall_efficiency: states_base.SimulationArray = [0.0]

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

        self.t.append(self.t[-1] + d_t)

        web_last = self.web[-1]
        self.burn_area.append(self.motor.grain.get_burn_area(web_last))
        self.propellant_volume.append(self.motor.grain.get_propellant_volume(web_last))
        burn_rate = self.motor.propellant.get_burn_rate(self.chamber_pressure[-1])
        self.burn_rate.append(burn_rate)
        self.web.append(web_last + burn_rate * (self.t[-1] - self.t[-2]))

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
        divergent_loss = losses.get_nozzle_divergent_percentage_loss(
            divergent_angle=nozzle.divergent_angle,
        )
        kinetics_loss = losses.get_kinetics_percentage_loss(
            i_sp_th_frozen=propellant_properties.i_sp_frozen,
            i_sp_th_shifting=propellant_properties.i_sp_shifting,
            chamber_pressure_psi=chamber_pressure_psi,
        )
        boundary_layer_loss = losses.get_boundary_layer_percentage_loss(
            chamber_pressure_psi=chamber_pressure_psi,
            throat_diameter_inch=throat_diameter_inch,
            expansion_ratio=nozzle.expansion_ratio,
            time=self.t[-1],
            c_1=nozzle.c_1,
            c_2=nozzle.c_2,
        )
        two_phase_loss = losses.get_two_phase_flow_percentage_loss(
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

        thrust_coefficient_ideal = nozzle_core.get_ideal_thrust_coefficient(
            new_chamber_pressure,
            self.exit_pressure[-1],
            external_pressure,
            nozzle.expansion_ratio,
            propellant_properties.k_exhaust,
        )
        thrust_coefficient = nozzle_core.apply_thrust_coefficient_correction(
            thrust_coefficient_ideal, overall_efficiency
        )
        self.thrust_coefficient.append(thrust_coefficient)
        self.thrust_coefficient_ideal.append(thrust_coefficient_ideal)
        self.thrust.append(
            nozzle_core.get_thrust_from_thrust_coefficient(
                thrust_coefficient, new_chamber_pressure, nozzle.get_throat_area()
            )
        )

        if self.propellant_mass[-1] <= 0 and not self.end_burn:
            self.burn_time = self.t[-1]
            self.end_burn = True
        if not isentropic.is_flow_choked(
            new_chamber_pressure,
            external_pressure,
            isentropic.get_critical_pressure_ratio(propellant_properties.k_chamber),
        ):
            self._thrust_time = self.t[-1]
            self.end_thrust = True

    def print_results(self) -> None:
        """
        Prints the results obtained during the SRM operation.
        """
        print("\nBURN REGRESSION")
        if self.propellant_mass[0] > 1:
            print(f" Propellant initial mass {self.propellant_mass[0]:.3f} kg")
        else:
            print(f" Propellant initial mass {self.propellant_mass[0] * 1e3:.3f} g")
        print(" Mean Kn: %.2f" % np.mean(self.klemmung))
        print(" Max Kn: %.2f" % np.max(self.klemmung))
        print(f" Initial to final Kn ratio: {self.initial_to_final_klemmung_ratio:.3f}")
        print(f" Volumetric efficiency: {self.volumetric_efficiency:.3%}")
        print(" Burn profile: " + self.burn_profile)
        print(
            f" Max initial mass flux: {self.max_mass_flux:.3f} kg/s-m-m or "
            f"{conversions.convert_mass_flux_metric_to_imperial(self.max_mass_flux):.3f} "
            "lb/s-in-in"
        )

        print("\nCHAMBER PRESSURE")
        print(
            f" Maximum, average chamber pressure: {np.max(self.chamber_pressure) * 1e-6:.3f}, "
            f"{np.mean(self.chamber_pressure) * 1e-6:.3f} MPa"
        )

        print("\nTHRUST AND IMPULSE")
        print(
            f" Maximum, average thrust: {np.max(self.thrust):.3f}, {np.mean(self.thrust):.3f} N"
        )
        print(
            f" Total, specific impulses: {self.total_impulse:.3f} N-s, {self.specific_impulse:.3f} s"
        )
        print(
            f" Burnout time, thrust time: {self.burn_time:.3f}, {self.thrust_time:.3f} s"
        )

        print("\nNOZZLE DESIGN")
        print(f" Average nozzle efficiency: {np.mean(self.nozzle_efficiency):.3%}")
        print(f" Average overall efficiency: {np.mean(self.overall_efficiency):.3%}")
        print(
            f" Divergent nozzle correction factor: {np.mean(self.divergent_loss):.3f}%"
        )
        print(
            f" Average kinetics correction factor: {np.mean(self.kinetics_loss):.3f}%"
        )
        print(
            f" Average boundary layer correction factor: {np.mean(self.boundary_layer_loss):.3f}%"
        )
        print(
            f" Average two-phase flow correction factor: {np.mean(self.two_phase_loss):.3f}%"
        )

    @property
    def klemmung(self) -> np.ndarray:
        """Get the klemmung values."""
        burn_area = np.asarray(self.burn_area)
        return (
            burn_area[burn_area > 0]
            / self.motor.thrust_chamber.nozzle.get_throat_area()
        )

    @property
    def initial_to_final_klemmung_ratio(self) -> float:
        """Get the ratio of the initial to final klemmung."""
        return self.klemmung[0] / self.klemmung[-1]

    @property
    def volumetric_efficiency(self) -> float:
        """Get the volumetric efficiency."""
        return (
            self.propellant_volume[0]
            / self.motor.thrust_chamber.combustion_chamber.internal_volume
        )

    @property
    def burn_profile(self) -> str:
        """Get the burn profile.

        Returns:
            Burn profile: "regressive", "progressive", or "neutral".
        """
        deviancy = 0.02
        burn_area_arr = np.asarray(self.burn_area)
        burn_area = burn_area_arr[burn_area_arr > 0]

        if burn_area[0] / burn_area[-1] > 1 + deviancy:
            return "regressive"
        elif burn_area[0] / burn_area[-1] < 1 - deviancy:
            return "progressive"
        else:
            return "neutral"

    @property
    def max_mass_flux(self) -> float:
        """Get the maximum mass flux."""
        return np.max(self.grain_mass_flux)

    @property
    def grain_mass_flux(self) -> np.ndarray:
        """Get the grain mass flux."""
        return self.motor.grain.get_mass_flux_per_segment(
            np.asarray(self.burn_rate),
            self.motor.propellant.ideal_density,
            np.asarray(self.web),
        )

    @property
    def total_impulse(self) -> float:
        """Get the total impulse [N-s]."""
        return performance.get_total_impulse_trapezoidal(
            np.asarray(self.thrust), np.asarray(self.t)
        )

    @property
    def specific_impulse(self) -> float:
        """Get the specific impulse [s]."""
        return performance.get_specific_impulse(
            total_impulse=self.total_impulse,
            initial_propellant_mass=self.propellant_mass[0],
        )
