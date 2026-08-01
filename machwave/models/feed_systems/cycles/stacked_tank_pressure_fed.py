import typing
from typing import Callable

import numpy as np
import scipy.optimize as optimize

import machwave.core.incompressible_flow as incompressible_flow
import machwave.models.feed_systems.base as feed_system_base
import machwave.models.feed_systems.tank as tank
import machwave.models.thrust_chamber.injector as injector_models

# Relative width the solved feed line flow is resolved to. The flow feeds a
# chamber pressure integration, which this is far finer than.
FEEDLINE_FLOW_TOLERANCE = 1e-4


class StackedTankPressureFedFeedSystem(feed_system_base.FeedSystem):
    """
    Represents a bipropellant biliquid rocket engine feed system with stacked tanks.

    A stacked tank system is a type of pressure-fed system where the oxidizer and fuel
    tanks are arranged in a vertical stack. The tanks are separated by a piston and the
    fuel is pressurized by the oxidizer tank.
    """

    def __init__(
        self,
        oxidizer_line_diameter: float,
        oxidizer_line_length: float,
        fuel_line_diameter: float,
        fuel_line_length: float,
        fuel_tank: tank.Tank,
        oxidizer_tank: tank.Tank,
        piston_loss: float = 0.0,
        oxidizer_line_loss_coefficient: float = 0.0,
        fuel_line_loss_coefficient: float = 0.0,
    ):
        """
        Initialize the StackedTankPressureFedFeedSystem.

        Args:
            oxidizer_line_diameter: Internal diameter of the oxidizer feedline [m].
            oxidizer_line_length: Length of the oxidizer feedline [m]. Zero
                leaves the oxidizer line out of the pressure budget.
            fuel_line_diameter: Internal diameter of the fuel feedline [m].
            fuel_line_length: Length of the fuel feedline [m]. Zero leaves the
                fuel line out of the pressure budget.
            fuel_tank: An instance representing the fuel tank.
            oxidizer_tank: An instance representing the oxidizer tank.
            piston_loss: Pressure loss across the piston [Pa]. Default is 0.0.
            oxidizer_line_loss_coefficient: Summed resistance coefficient of the
                valves and bends on the oxidizer line.
            fuel_line_loss_coefficient: Summed resistance coefficient of the
                valves and bends on the fuel line.

        Raises:
            ValueError: If any argument is outside its valid physical range.
        """
        super().__init__(fuel_tank, oxidizer_tank)

        self.oxidizer_line_diameter = oxidizer_line_diameter
        self.oxidizer_line_length = oxidizer_line_length
        self.fuel_line_diameter = fuel_line_diameter
        self.fuel_line_length = fuel_line_length

        self.piston_loss = piston_loss
        self.oxidizer_line_loss_coefficient = oxidizer_line_loss_coefficient
        self.fuel_line_loss_coefficient = fuel_line_loss_coefficient

        self.fuel_tank = fuel_tank
        self.oxidizer_tank = oxidizer_tank

        self._validate()

    def _validate(self) -> None:
        """
        Validate the feed line inputs.

        Raises:
            ValueError: If any field is outside its valid physical range.
        """
        for name, value in (
            ("oxidizer_line_diameter", self.oxidizer_line_diameter),
            ("fuel_line_diameter", self.fuel_line_diameter),
        ):
            if value <= 0.0:
                raise ValueError(f"{name} must be strictly positive, got {value}")

        for name, value in (
            ("oxidizer_line_length", self.oxidizer_line_length),
            ("fuel_line_length", self.fuel_line_length),
            ("piston_loss", self.piston_loss),
            (
                "oxidizer_line_loss_coefficient",
                self.oxidizer_line_loss_coefficient,
            ),
            ("fuel_line_loss_coefficient", self.fuel_line_loss_coefficient),
        ):
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative, got {value}")

    def get_mass_flow_ox(
        self,
        chamber_pressure: float,
        *,
        injector: injector_models.BipropellantInjector,
        oxidizer_mass: float,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Compute the current oxidizer mass flow rate by delegating to the injector.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.

        Returns:
            Oxidizer mass flow rate [kg/s].
        """
        return self._solve_line_limited_mass_flow(
            get_mass_flow=lambda pressure_upstream: injector.get_mass_flow_ox(
                tank=self.oxidizer_tank,
                pressure_upstream=pressure_upstream,
                chamber_pressure=chamber_pressure,
                fluid_mass=oxidizer_mass,
                internal_energy=oxidizer_internal_energy,
            ),
            get_delivered_pressure=lambda mass_flow_rate: (
                self.get_oxidizer_tank_pressure(
                    oxidizer_mass=oxidizer_mass,
                    mass_flow_rate=mass_flow_rate,
                    oxidizer_internal_energy=oxidizer_internal_energy,
                )
            ),
            chamber_pressure=chamber_pressure,
        )

    def get_mass_flow_fuel(
        self,
        chamber_pressure: float,
        *,
        injector: injector_models.BipropellantInjector,
        fuel_mass: float,
        oxidizer_mass: float,
        fuel_internal_energy: float | None = None,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Compute the current fuel mass flow rate by delegating to the injector.

        The upstream pressure is the oxidizer tank pressure minus the piston
        loss, since this models a stacked tank pressurized through the piston.

        Args:
            chamber_pressure: Chamber pressure [Pa].
            injector: Bipropellant injector handling the orifice dispatch.
            fuel_mass: Current fuel mass in the tank [kg].
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            fuel_internal_energy: Current internal energy of the fuel [J].
                Required for a tank running an energy balance, unused
                otherwise.
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J], which pressurizes the fuel through the piston. Required
                for a tank running an energy balance, unused otherwise.

        Returns:
            Fuel mass flow rate [kg/s].
        """
        return self._solve_line_limited_mass_flow(
            get_mass_flow=lambda pressure_upstream: injector.get_mass_flow_fuel(
                tank=self.fuel_tank,
                pressure_upstream=pressure_upstream,
                chamber_pressure=chamber_pressure,
                fluid_mass=fuel_mass,
                internal_energy=fuel_internal_energy,
            ),
            get_delivered_pressure=lambda mass_flow_rate: self.get_fuel_tank_pressure(
                oxidizer_mass=oxidizer_mass,
                fuel_mass=fuel_mass,
                mass_flow_rate=mass_flow_rate,
                fuel_internal_energy=fuel_internal_energy,
                oxidizer_internal_energy=oxidizer_internal_energy,
            ),
            chamber_pressure=chamber_pressure,
        )

    def get_oxidizer_tank_pressure(
        self,
        *,
        oxidizer_mass: float,
        mass_flow_rate: float = 0.0,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Returns the oxidizer-side pressure delivered to the injector [Pa].

        The tank pressure less what the oxidizer line takes in friction at the
        given flow. At rest the line takes nothing and this is the tank
        pressure itself.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            mass_flow_rate: Oxidizer flow through the line [kg/s].
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J]. Required for a tank running an energy balance, unused
                otherwise.
        """
        return self.oxidizer_tank.get_pressure(
            oxidizer_mass, oxidizer_internal_energy
        ) - self._get_line_pressure_drop(
            propellant_tank=self.oxidizer_tank,
            fluid_mass=oxidizer_mass,
            internal_energy=oxidizer_internal_energy,
            mass_flow_rate=mass_flow_rate,
            length=self.oxidizer_line_length,
            diameter=self.oxidizer_line_diameter,
            loss_coefficient=self.oxidizer_line_loss_coefficient,
        )

    def get_fuel_tank_pressure(
        self,
        *,
        oxidizer_mass: float,
        fuel_mass: float,
        mass_flow_rate: float = 0.0,
        fuel_internal_energy: float | None = None,
        oxidizer_internal_energy: float | None = None,
    ) -> float:
        """
        Returns the fuel-side pressure delivered to the injector [Pa].

        In a stacked-tank system the fuel is pressurized by the oxidizer
        through the piston, so the fuel side starts from the oxidizer tank
        pressure less the piston pressure loss, and then loses what the fuel
        line takes in friction at the given flow. The oxidizer line is not on
        this path.

        Args:
            oxidizer_mass: Current oxidizer mass in the tank [kg].
            fuel_mass: Current fuel mass in the tank [kg].
            mass_flow_rate: Fuel flow through the line [kg/s].
            fuel_internal_energy: Current internal energy of the fuel [J].
                Required for a tank running an energy balance, unused
                otherwise.
            oxidizer_internal_energy: Current internal energy of the oxidizer
                [J], which sets the pressure the piston passes on. Required for
                a tank running an energy balance, unused otherwise.
        """
        return (
            self.oxidizer_tank.get_pressure(oxidizer_mass, oxidizer_internal_energy)
            - self.piston_loss
            - self._get_line_pressure_drop(
                propellant_tank=self.fuel_tank,
                fluid_mass=fuel_mass,
                internal_energy=fuel_internal_energy,
                mass_flow_rate=mass_flow_rate,
                length=self.fuel_line_length,
                diameter=self.fuel_line_diameter,
                loss_coefficient=self.fuel_line_loss_coefficient,
            )
        )

    @staticmethod
    def _get_line_pressure_drop(
        *,
        propellant_tank: tank.Tank,
        fluid_mass: float,
        internal_energy: float | None,
        mass_flow_rate: float,
        length: float,
        diameter: float,
        loss_coefficient: float,
    ) -> float:
        """Friction pressure drop along one feed line [Pa]."""
        if mass_flow_rate <= 0.0 or length <= 0.0:
            return 0.0

        if not propellant_tank.is_delivering_liquid(fluid_mass, internal_energy):
            # A tank down to its vapor feeds a compressible flow, which this
            # incompressible line model has nothing to say about.
            return 0.0

        return incompressible_flow.get_pipe_pressure_drop(
            density=propellant_tank.get_density(fluid_mass, internal_energy),
            mass_flow_rate=mass_flow_rate,
            length=length,
            diameter=diameter,
            dynamic_viscosity=propellant_tank.get_dynamic_viscosity(
                fluid_mass, internal_energy
            ),
            loss_coefficient=loss_coefficient,
        )

    @staticmethod
    def _solve_line_limited_mass_flow(
        *,
        get_mass_flow: Callable[[float], float],
        get_delivered_pressure: Callable[[float], float],
        chamber_pressure: float,
    ) -> float:
        """
        Solve the flow that balances the line drop against the injector demand.

        The drop along the line grows with the flow while the flow falls with
        the drop, so the two are implicit in each other. Their balance is the
        root of the demand less the assumed flow, which only falls as the
        assumed flow rises: it starts positive at rest, where the line takes
        nothing and the injector asks for everything, and ends non-positive at
        the flow the injector would draw through no line at all. That brackets
        the root, so it is bisected rather than iterated, which a line taking
        more than half the head would send oscillating past the answer.

        A flow the line cannot deliver above the chamber pressure has no
        forward flow behind it, and counts as a demand of nothing rather than a
        negative drop through the injector.

        Args:
            get_mass_flow: Injector flow for a pressure at its inlet [kg/s].
            get_delivered_pressure: Pressure at the injector inlet for a flow
                through the line [Pa].
            chamber_pressure: Chamber pressure [Pa].

        Returns:
            Mass flow rate through the line [kg/s].
        """

        def get_flow_imbalance(mass_flow_rate: float) -> float:
            delivered_pressure = get_delivered_pressure(mass_flow_rate)
            if delivered_pressure <= chamber_pressure:
                return -mass_flow_rate
            return get_mass_flow(delivered_pressure) - mass_flow_rate

        lossless_mass_flow_rate = get_flow_imbalance(0.0)
        if lossless_mass_flow_rate <= 0.0:
            return 0.0

        if get_flow_imbalance(lossless_mass_flow_rate) >= 0.0:
            # The line takes nothing off the flow it would draw without one.
            return lossless_mass_flow_rate

        return typing.cast(
            float,
            optimize.brentq(
                get_flow_imbalance,
                0.0,
                lossless_mass_flow_rate,
                rtol=np.float64(FEEDLINE_FLOW_TOLERANCE),
            ),
        )
