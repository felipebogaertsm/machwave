import machwave.core.compressible_flow.losses as losses_core
import machwave.models.losses.base as losses_base
import machwave.models.propellants as propellants

_SOLID = propellants.MixtureType.SOLID
_BILIQUID = propellants.MixtureType.BILIQUID
_BOTH = losses_base.ThrustCoefficientTermTarget.BOTH
_MOMENTUM = losses_base.ThrustCoefficientTermTarget.MOMENTUM


class DivergenceLoss(losses_base.LossComponent):
    """Nozzle divergence loss; derates the momentum term only."""

    name = "divergent_loss"
    applicable_mixture_types = frozenset({_SOLID, _BILIQUID})
    default_target = _MOMENTUM

    def get_loss_fraction(self, context: losses_base.LossEvaluationContext) -> float:
        return losses_core.get_nozzle_divergent_loss_fraction(
            divergent_angle=context.nozzle.divergent_angle
        )


class KineticsLoss(losses_base.LossComponent):
    """Finite-rate chemistry (nozzle kinetics) loss."""

    name = "kinetics_loss"
    applicable_mixture_types = frozenset({_SOLID, _BILIQUID})
    default_target = _BOTH

    def get_loss_fraction(self, context: losses_base.LossEvaluationContext) -> float:
        return losses_core.get_kinetics_loss_fraction(
            i_sp_th_frozen=context.properties.i_sp_frozen,
            i_sp_th_shifting=context.properties.i_sp_shifting,
            chamber_pressure_psi=context.chamber_pressure_psi,
        )


class BoundaryLayerLoss(losses_base.LossComponent):
    """Boundary-layer loss, calibrated for solid motors."""

    name = "boundary_layer_loss"
    applicable_mixture_types = frozenset({_SOLID})
    default_target = _BOTH

    def get_loss_fraction(self, context: losses_base.LossEvaluationContext) -> float:
        return losses_core.get_boundary_layer_loss_fraction(
            chamber_pressure_psi=context.chamber_pressure_psi,
            throat_diameter_inch=context.throat_diameter_inch,
            expansion_ratio=context.nozzle.expansion_ratio,
            time=context.time,
            c_1=context.nozzle.c_1,
            c_2=context.nozzle.c_2,
        )


class TwoPhaseFlowLoss(losses_base.LossComponent):
    """Two-phase (condensed-phase) flow loss, for solid motors."""

    name = "two_phase_loss"
    applicable_mixture_types = frozenset({_SOLID})
    default_target = _BOTH

    def get_loss_fraction(self, context: losses_base.LossEvaluationContext) -> float:
        return losses_core.get_two_phase_flow_loss_fraction(
            chamber_pressure_psi=context.chamber_pressure_psi,
            mass_fraction_of_condensed_phase=context.properties.qsi_chamber,
            expansion_ratio=context.nozzle.expansion_ratio,
            throat_diameter_inch=context.throat_diameter_inch,
            characteristic_length_inch=context.characteristic_length_inch,
        )


class ConstantFractionLoss(losses_base.LossComponent):
    """A fixed loss fraction, independent of operating conditions."""

    applicable_mixture_types = frozenset({_SOLID, _BILIQUID})
    default_target = _BOTH

    def __init__(
        self,
        fraction: float,
        *,
        name: str,
        target: losses_base.ThrustCoefficientTermTarget | None = None,
    ) -> None:
        """
        Initialize a constant loss.

        Args:
            fraction: Loss fraction in [0, 1].
            name: Diagnostic series name.
            target: Thrust-coefficient term to derate.

        Raises:
            ValueError: If `fraction` is outside [0, 1].
        """
        super().__init__(target=target)
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"loss fraction must be in [0, 1], got {fraction}.")
        self.name = name
        self.fraction = fraction

    def get_loss_fraction(self, context: losses_base.LossEvaluationContext) -> float:
        return self.fraction
