import numpy as np

from machwave.models.propulsion.motors import LiquidEngine
from machwave.operations.internal_ballistics.base import MotorOperation
from machwave.services.equations import solve_pressure_fed_lre_chamber_pressure
from machwave.solvers.odes import rk4th_ode_solver
from machwave.services.flow.isentropic import (
    get_thrust_coefficients,
    get_thrust_from_cf,
    is_flow_choked,
    get_critical_pressure_ratio,
    get_exit_pressure,
)


class LiquidEngineOperation(MotorOperation):
    """
    Operation for a Liquid Rocket Engine.

    The variable names correspond to what they are commonly referred to in books and papers related to
    Rocket Propulsion. Therefore, PEP8's snake_case will not be followed rigorously.
    """

    motor: LiquidEngine

    def __init__(
        self,
        motor: LiquidEngine,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
    ) -> None:
        """
        Initial parameters for a SRM operation.
        """
        super().__init__(
            motor=motor,
            initial_pressure=initial_pressure,
            initial_atmospheric_pressure=initial_atmospheric_pressure,
        )

        self.oxidizer_mass = np.array([motor.feed_system.oxidizer_tank.fluid_mass])
        self.fuel_mass = np.array([motor.feed_system.fuel_tank.fluid_mass])
        self.n_cf = np.array([0])  # thrust coefficient correction factor

    def iterate(
        self,
        d_t: float,
        P_ext: float,
    ) -> None:
        """
        Iterate liquid engine operation.

        Args:
            d_t: Time step.
            P_ext: External pressure.

        TODO: update this method.
        """
        if not self.end_thrust:
            self.t = np.append(self.t, self.t[-1] + d_t)  # append new time value

            self.motor.propellant.update_properties(
                chamber_pressure=self.P_0[-1],
                eps=self.motor.thrust_chamber.nozzle.expansion_ratio,
            )  # update propellant properties based on chamber pressure from last iteration

            fuel_mass_flow = self.motor.feed_system.get_mass_flow_fuel(
                chamber_pressure=self.P_0[-1],
                discharge_coefficient=self.motor.thrust_chamber.injector.discharge_coefficient_fuel,
                injector_area=self.motor.thrust_chamber.injector.area_fuel,
            )

            ox_mass_flow = self.motor.feed_system.get_mass_flow_ox(
                chamber_pressure=self.P_0[-1],
                discharge_coefficient=self.motor.thrust_chamber.injector.discharge_coefficient_oxidizer,
                injector_area=self.motor.thrust_chamber.injector.area_ox,
            )

            P0 = rk4th_ode_solver(
                variables={"P0": self.P_0[-1]},
                equation=solve_pressure_fed_lre_chamber_pressure,
                d_t=d_t,
                R=self.motor.propellant.R_chamber,
                T0=self.motor.propellant.combustion_temperature,
                V0=self.motor.thrust_chamber.combustion_chamber.empty_volume,
                At=self.motor.thrust_chamber.nozzle.get_throat_area(),
                k=self.motor.propellant.chamber_gamma,
                m_dot_ox=ox_mass_flow,
                m_dot_fuel=fuel_mass_flow,
            )[0]
            self.P_0 = np.append(self.P_0, P0)  # calculate new chamber pressure

            P_exit = get_exit_pressure(
                self.motor.propellant.exit_gamma,
                self.motor.thrust_chamber.nozzle.expansion_ratio,
                self.P_0[-1],
            )
            self.P_exit = np.append(
                self.P_exit,
                P_exit,
            )  # calculate new exit pressure

            self.n_cf = np.append(
                self.n_cf, 1
            )  # TODO: calculate new thrust coefficient correction

            C_f, C_f_ideal = get_thrust_coefficients(
                self.P_0[-1],
                self.P_exit[-1],
                P_ext,
                self.motor.thrust_chamber.nozzle.expansion_ratio,
                self.motor.propellant.exit_gamma,
                self.n_cf[-1],
            )
            self.C_f = np.append(self.C_f, C_f)
            self.C_f_ideal = np.append(self.C_f_ideal, C_f_ideal)
            thrust = get_thrust_from_cf(
                C_f,
                self.P_0[-1],
                self.motor.thrust_chamber.nozzle.get_throat_area(),
            )
            self.thrust = np.append(self.thrust, thrust)  # in N

            self.oxidizer_mass = np.append(
                self.oxidizer_mass,
                self.oxidizer_mass[-1] - ox_mass_flow * d_t,
            )
            self.fuel_mass = np.append(
                self.fuel_mass,
                self.fuel_mass[-1] - fuel_mass_flow * d_t,
            )
            self.m_prop = np.append(
                self.m_prop,
                self.oxidizer_mass[-1] + self.fuel_mass[-1],
            )  # update propellant mass

            if self.m_prop[-1] == 0 and not self.end_burn:
                self.burn_time = self.t[-1]
                self.end_burn = True

            # This if statement changes 'end_thrust' to True if supersonic
            # flow is not achieved anymore.
            if not is_flow_choked(
                self.P_0[-1],
                P_ext,
                get_critical_pressure_ratio(self.motor.propellant.chamber_gamma),
            ):
                self._thrust_time = self.t[-1]
                self.end_thrust = True

    def print_results(self) -> None:
        """
        TODO: implement this method.
        """
