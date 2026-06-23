import machwave.models.feed_systems.base as feed_system_base
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants as propellants
import machwave.models.thrust_chamber as thrust_chamber_models

from . import base as motor_base


class BiliquidEngine(
    motor_base.Motor[
        propellants.BiliquidPropellant,
        thrust_chamber_models.BiliquidEngineThrustChamber,
    ]
):
    """Biliquid rocket engine with a bipropellant feed system."""

    def __init__(
        self,
        propellant: propellants.BiliquidPropellant,
        thrust_chamber: thrust_chamber_models.BiliquidEngineThrustChamber,
        feed_system: feed_system_base.FeedSystem,
        combustion_efficiency: float = 0.95,
        nozzle_loss_model: nozzle_losses.NozzleLossModel | None = None,
    ) -> None:
        """
        Initialize a biliquid rocket engine.

        Args:
            propellant: Biliquid propellant properties (oxidizer + fuel).
            thrust_chamber: Thrust chamber assembly (nozzle, combustion chamber,
                injector).
            feed_system: Propellant feed system (tanks, lines, pumps or
                pressurization).
            combustion_efficiency: Ratio of the actual flame temperature to the ideal
                adiabatic flame temperature (0, 1].
            nozzle_loss_model: Nozzle loss model.
        """
        super().__init__(
            propellant,
            thrust_chamber,
            combustion_efficiency,
            nozzle_loss_model=nozzle_loss_model
            or nozzle_losses.presets.constant_efficiency_loss_model(
                mixture_type=propellants.MixtureType.BILIQUID
            ),
        )
        self.feed_system = feed_system

    @property
    def initial_propellant_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        return self.feed_system.get_initial_propellant_mass()
