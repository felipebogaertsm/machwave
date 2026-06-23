import machwave.models.grain as grain
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.propellants as propellants
import machwave.models.thrust_chamber as thrust_chamber

from . import base as motor_base


class SolidMotor(
    motor_base.Motor[
        propellants.SolidPropellant, thrust_chamber.SolidMotorThrustChamber
    ]
):
    """Solid rocket motor with a propellant grain and thrust chamber."""

    def __init__(
        self,
        grain: grain.Grain,
        propellant: propellants.SolidPropellant,
        thrust_chamber: thrust_chamber.SolidMotorThrustChamber,
        combustion_efficiency: float = 0.95,
        nozzle_loss_model: nozzle_losses.NozzleLossModel | None = None,
    ) -> None:
        """
        Initialize a solid rocket motor.

        Args:
            grain: Grain geometry configuration.
            propellant: Solid propellant properties.
            thrust_chamber: Thrust chamber model.
            combustion_efficiency: Ratio of the actual flame temperature to the ideal
                adiabatic flame temperature (0, 1].
            nozzle_loss_model: Nozzle loss model.
        """
        super().__init__(
            propellant,
            thrust_chamber,
            combustion_efficiency,
            nozzle_loss_model=nozzle_loss_model
            or nozzle_losses.presets.spp1975_solid_loss_model(),
        )

        self.grain = grain
        self.propellant: propellants.SolidPropellant = propellant

    def get_free_chamber_volume(self, propellant_volume: float) -> float:
        """
        Return the chamber volume without any propellant.

        Args:
            propellant_volume: Propellant volume [m^3].

        Returns:
            Free chamber volume [m^3].
        """
        return (
            self.thrust_chamber.combustion_chamber.internal_volume - propellant_volume
        )

    @property
    def initial_propellant_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        return self.grain.get_propellant_mass(
            web_distance=0, ideal_density=self.propellant.ideal_density
        )
