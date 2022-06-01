# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


def _test_combustion_chamber_properties(combustion_chamber):
    """
    Generic test function for CombustionChamber and its descendents.

    Tests geometric properties of the class, such as inner radius
    (calculated from inner diameter) and more.
    """
    inner_diameter = combustion_chamber.inner_diameter
    assert inner_diameter > 0
    assert (
        inner_diameter
        == combustion_chamber.casing_inner_diameter
        - 2 * combustion_chamber.liner.thickness
    )

    assert combustion_chamber.inner_radius == inner_diameter / 2
    assert (
        combustion_chamber.outer_radius
        == combustion_chamber.outer_diameter / 2
    )

    assert (
        combustion_chamber.casing_inner_diameter
        == inner_diameter + 2 * combustion_chamber.liner.thickness
    )


def test_combustion_chamber_properties(combustion_chamber_olympus):
    _test_combustion_chamber_properties(combustion_chamber_olympus)


def test_bolted_combustion_chamber_properties(
    bolted_combustion_chamber_olympus,
):
    _test_combustion_chamber_properties(bolted_combustion_chamber_olympus)
