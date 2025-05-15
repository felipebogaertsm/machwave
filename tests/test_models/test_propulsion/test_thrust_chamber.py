def _test_combustion_chamber_properties(combustion_chamber_olympus):
    """
    Generic test function for CombustionChamber and its descendents.

    Tests geometric properties of the class, such as inner radius
    (calculated from inner diameter) and more.
    """
    net = combustion_chamber_olympus.inner_diameter
    gross = combustion_chamber_olympus.casing_inner_diameter

    assert net > 0
    assert net == gross - 2 * combustion_chamber_olympus.thermal_liner_thickness

    assert combustion_chamber_olympus.inner_radius == net / 2
    assert (
        combustion_chamber_olympus.outer_radius
        == combustion_chamber_olympus.outer_diameter / 2
    )

    assert gross == net + 2 * combustion_chamber_olympus.liner.thickness
