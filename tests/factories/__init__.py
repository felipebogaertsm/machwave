"""Reusable factories for building model instances in tests.

Each factory exposes a ``build(**overrides)`` classmethod that returns a model
instance with sensible defaults; tests only specify the fields they actually
care about. Composite factories (motors, thrust chambers, feed systems)
delegate sub-component construction to lower-level factories so an override
can be applied at any layer.
"""

from tests.factories.feed_systems import (
    StackedTankPressureFedFeedSystemFactory,
    TankFactory,
)
from tests.factories.grain import (
    BatesSegmentFactory,
    ConicalGrainSegmentFactory,
    DGrainSegmentFactory,
    MultiPortGrainSegmentFactory,
    RodAndTubeGrainSegmentFactory,
    StarGrainSegmentFactory,
    WagonWheelGrainSegmentFactory,
)
from tests.factories.motors import (
    LiquidEngineFactory,
    SolidMotorFactory,
)
from tests.factories.propellants import (
    BiliquidPropellantFactory,
    FuelComponentFactory,
    LiquidPropellantPropertiesFactory,
    OxidizerComponentFactory,
    SolidPropellantPropertiesFactory,
)
from tests.factories.thrust_chamber import (
    BipropellantInjectorFactory,
    CombustionChamberFactory,
    LiquidEngineThrustChamberFactory,
    NozzleFactory,
    SolidMotorThrustChamberFactory,
)

__all__ = [
    "BatesSegmentFactory",
    "BiliquidPropellantFactory",
    "BipropellantInjectorFactory",
    "CombustionChamberFactory",
    "ConicalGrainSegmentFactory",
    "DGrainSegmentFactory",
    "FuelComponentFactory",
    "LiquidEngineFactory",
    "LiquidEngineThrustChamberFactory",
    "LiquidPropellantPropertiesFactory",
    "MultiPortGrainSegmentFactory",
    "NozzleFactory",
    "OxidizerComponentFactory",
    "RodAndTubeGrainSegmentFactory",
    "SolidMotorFactory",
    "SolidMotorThrustChamberFactory",
    "SolidPropellantPropertiesFactory",
    "StackedTankPressureFedFeedSystemFactory",
    "StarGrainSegmentFactory",
    "TankFactory",
    "WagonWheelGrainSegmentFactory",
]
