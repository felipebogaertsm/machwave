"""Factories for grain-segment model instances."""

from __future__ import annotations

from typing import Any

from machwave.models.grain import geometries as grain_geometries


class BatesSegmentFactory:
    @classmethod
    def build(cls, **overrides: Any) -> grain_geometries.BatesSegment:
        kwargs: dict[str, Any] = dict(
            outer_diameter=0.1,
            core_diameter=0.04,
            length=0.2,
            density_ratio=1.0,
        )
        kwargs.update(overrides)
        return grain_geometries.BatesSegment(**kwargs)


class StarGrainSegmentFactory:
    @classmethod
    def build(cls, **overrides: Any) -> grain_geometries.StarGrainSegment:
        kwargs: dict[str, Any] = dict(
            length=1.0,
            outer_diameter=0.1,
            number_of_points=5,
            point_length=0.035,
            point_width=0.01,
            density_ratio=1.0,
        )
        kwargs.update(overrides)
        return grain_geometries.StarGrainSegment(**kwargs)


class WagonWheelGrainSegmentFactory:
    @classmethod
    def build(cls, **overrides: Any) -> grain_geometries.WagonWheelGrainSegment:
        kwargs: dict[str, Any] = dict(
            length=1.0,
            outer_diameter=0.1,
            core_diameter=0.02,
            number_of_ports=6,
            port_inner_diameter=0.03,
            port_outer_diameter=0.045,
            port_angular_width=0.1,
            density_ratio=1.0,
        )
        kwargs.update(overrides)
        return grain_geometries.WagonWheelGrainSegment(**kwargs)


class RodAndTubeGrainSegmentFactory:
    @classmethod
    def build(cls, **overrides: Any) -> grain_geometries.RodAndTubeGrainSegment:
        kwargs: dict[str, Any] = dict(
            length=1.0,
            outer_diameter=0.1,
            rod_outer_diameter=0.01,
            tube_inner_diameter=0.03,
            density_ratio=1.0,
        )
        kwargs.update(overrides)
        return grain_geometries.RodAndTubeGrainSegment(**kwargs)


class MultiPortGrainSegmentFactory:
    @classmethod
    def build(cls, **overrides: Any) -> grain_geometries.MultiPortGrainSegment:
        kwargs: dict[str, Any] = dict(
            length=1.0,
            outer_diameter=0.1,
            port_diameter=0.015,
            port_radial_count=3,
            port_level_count=1,
            density_ratio=1.0,
        )
        kwargs.update(overrides)
        return grain_geometries.MultiPortGrainSegment(**kwargs)


class DGrainSegmentFactory:
    @classmethod
    def build(cls, **overrides: Any) -> grain_geometries.DGrainSegment:
        kwargs: dict[str, Any] = dict(
            length=1.0,
            outer_diameter=0.1,
            slot_offset=0.02,
            density_ratio=1.0,
        )
        kwargs.update(overrides)
        return grain_geometries.DGrainSegment(**kwargs)


class ConicalGrainSegmentFactory:
    @classmethod
    def build(cls, **overrides: Any) -> grain_geometries.ConicalGrainSegment:
        kwargs: dict[str, Any] = dict(
            length=1.0,
            outer_diameter=0.1,
            upper_core_diameter=0.04,
            lower_core_diameter=0.04,
            density_ratio=1.0,
        )
        kwargs.update(overrides)
        return grain_geometries.ConicalGrainSegment(**kwargs)
