"""
Locks the top-level ``machwave`` namespace re-exports introduced for issue #172.

These re-exports are user-facing API; if a deep path is renamed or moved, the
top-level binding must follow.
"""

import machwave
import machwave.models.feed_systems
import machwave.models.grain
import machwave.models.grain.geometries
import machwave.models.motors
import machwave.models.propellants
import machwave.models.propellants.formulations
import machwave.models.propellants.formulations.biliquid
import machwave.models.propellants.formulations.solid
import machwave.models.thrust_chamber
import machwave.simulation


def test_top_level_namespaces_are_canonical_modules():
    assert machwave.feed_systems is machwave.models.feed_systems
    assert machwave.formulations is machwave.models.propellants.formulations
    assert machwave.grain is machwave.models.grain
    assert machwave.motors is machwave.models.motors
    assert machwave.propellants is machwave.models.propellants
    assert machwave.simulation is machwave.simulation
    assert machwave.thrust_chamber is machwave.models.thrust_chamber


def test_grain_exposes_geometries_subnamespace():
    assert machwave.grain.geometries is machwave.models.grain.geometries


def test_formulations_exposes_solid_and_biliquid():
    assert machwave.formulations.solid is machwave.models.propellants.formulations.solid
    assert (
        machwave.formulations.biliquid
        is machwave.models.propellants.formulations.biliquid
    )
