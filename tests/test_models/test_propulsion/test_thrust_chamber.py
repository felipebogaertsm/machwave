def _test_combustion_chamber_properties(combustion_chamber):
    """
    Generic test function for CombustionChamber and its descendents.

    Tests geometric properties of the class, such as inner radius
    (calculated from inner diameter) and more.
    """
    net = combustion_chamber.inner_diameter
    gross = combustion_chamber.casing_inner_diameter

    assert net > 0
    assert net == gross - 2 * combustion_chamber.liner.thickness

    assert combustion_chamber.inner_radius == net / 2
    assert combustion_chamber.outer_radius == combustion_chamber.outer_diameter / 2

    assert gross == net + 2 * combustion_chamber.liner.thickness


def test_combustion_chamber_properties(combustion_chamber_olympus):
    _test_combustion_chamber_properties(combustion_chamber_olympus)


def test_bolted_combustion_chamber_properties(
    bolted_combustion_chamber_olympus,
):
    _test_combustion_chamber_properties(bolted_combustion_chamber_olympus)
