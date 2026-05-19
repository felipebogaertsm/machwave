"""Construction and validation tests for the feed-system component specifications."""

import dataclasses

import pytest

from machwave.models.feed_systems.components import (
    GasGeneratorSpec,
    PumpSpec,
    RegenerativeJacketSpec,
    TurbineSpec,
)


def _valid_pump_spec_kwargs() -> dict:
    """Return a dictionary of valid keyword arguments for `PumpSpec`."""
    return dict(
        name="oxidizer pump",
        isentropic_efficiency=0.7,
        pressure_rise=5.0e6,
        volumetric_flow_design=2.0e-3,
        shaft_speed_design=3000.0,
    )


def _valid_turbine_spec_kwargs() -> dict:
    """Return a dictionary of valid keyword arguments for `TurbineSpec`."""
    return dict(
        name="oxidizer turbine",
        isentropic_efficiency=0.65,
        pressure_ratio=20.0,
        inlet_temperature_design=900.0,
        mass_flow_design=1.5,
    )


def _valid_gas_generator_spec_kwargs() -> dict:
    """Return a dictionary of valid keyword arguments for `GasGeneratorSpec`."""
    return dict(
        name="gas generator",
        mixture_ratio=0.3,
        chamber_pressure=8.0e6,
        gas_temperature=900.0,
        mass_flow=2.0,
    )


def _valid_regenerative_jacket_spec_kwargs() -> dict:
    """Return a dictionary of valid keyword arguments for `RegenerativeJacketSpec`."""
    return dict(
        name="chamber jacket",
        pressure_drop=1.0e6,
        coolant_temperature_rise=200.0,
        heat_pickup=5.0e6,
    )


def test_pump_spec_constructs_with_valid_values():
    """A `PumpSpec` with valid fields must construct without error."""
    spec = PumpSpec(**_valid_pump_spec_kwargs())

    assert spec.name == "oxidizer pump"
    assert spec.isentropic_efficiency == pytest.approx(0.7)


def test_turbine_spec_constructs_with_valid_values():
    """A `TurbineSpec` with valid fields must construct without error."""
    spec = TurbineSpec(**_valid_turbine_spec_kwargs())

    assert spec.name == "oxidizer turbine"
    assert spec.pressure_ratio == pytest.approx(20.0)


def test_gas_generator_spec_constructs_with_valid_values():
    """A `GasGeneratorSpec` with valid fields must construct without error."""
    spec = GasGeneratorSpec(**_valid_gas_generator_spec_kwargs())

    assert spec.name == "gas generator"
    assert spec.mixture_ratio == pytest.approx(0.3)


def test_regenerative_jacket_spec_constructs_with_valid_values():
    """A `RegenerativeJacketSpec` with valid fields must construct without error."""
    spec = RegenerativeJacketSpec(**_valid_regenerative_jacket_spec_kwargs())

    assert spec.name == "chamber jacket"
    assert spec.coolant_temperature_rise == pytest.approx(200.0)


def test_pump_spec_rejects_efficiency_above_one():
    """Isentropic efficiency above one is unphysical and must raise."""
    kwargs = _valid_pump_spec_kwargs()
    kwargs["isentropic_efficiency"] = 1.5

    with pytest.raises(ValueError, match="isentropic_efficiency"):
        PumpSpec(**kwargs)


def test_pump_spec_rejects_non_positive_pressure_rise():
    """A non-positive pressure rise is unphysical and must raise."""
    kwargs = _valid_pump_spec_kwargs()
    kwargs["pressure_rise"] = 0.0

    with pytest.raises(ValueError, match="pressure_rise"):
        PumpSpec(**kwargs)


def test_turbine_spec_rejects_pressure_ratio_at_or_below_one():
    """A turbine with pressure ratio of one or less produces no work and must raise."""
    kwargs = _valid_turbine_spec_kwargs()
    kwargs["pressure_ratio"] = 1.0

    with pytest.raises(ValueError, match="pressure_ratio"):
        TurbineSpec(**kwargs)


def test_gas_generator_spec_rejects_temperature_above_metal_limit():
    """A gas-generator temperature above the documented limit must raise."""
    kwargs = _valid_gas_generator_spec_kwargs()
    kwargs["gas_temperature"] = 5000.0

    with pytest.raises(ValueError, match="gas_temperature"):
        GasGeneratorSpec(**kwargs)


def test_gas_generator_spec_rejects_non_positive_mixture_ratio():
    """A non-positive mixture ratio is unphysical and must raise."""
    kwargs = _valid_gas_generator_spec_kwargs()
    kwargs["mixture_ratio"] = 0.0

    with pytest.raises(ValueError, match="mixture_ratio"):
        GasGeneratorSpec(**kwargs)


def test_regenerative_jacket_spec_rejects_negative_pressure_drop():
    """A negative pressure drop across the jacket is unphysical and must raise."""
    kwargs = _valid_regenerative_jacket_spec_kwargs()
    kwargs["pressure_drop"] = -1.0

    with pytest.raises(ValueError, match="pressure_drop"):
        RegenerativeJacketSpec(**kwargs)


def test_regenerative_jacket_spec_rejects_non_positive_temperature_rise():
    """The coolant must always heat up across the jacket; zero rise must raise."""
    kwargs = _valid_regenerative_jacket_spec_kwargs()
    kwargs["coolant_temperature_rise"] = 0.0

    with pytest.raises(ValueError, match="coolant_temperature_rise"):
        RegenerativeJacketSpec(**kwargs)


@pytest.mark.parametrize(
    "spec_class, kwargs_builder, field_name, new_value",
    [
        (PumpSpec, _valid_pump_spec_kwargs, "name", "modified pump"),
        (TurbineSpec, _valid_turbine_spec_kwargs, "name", "modified turbine"),
        (
            GasGeneratorSpec,
            _valid_gas_generator_spec_kwargs,
            "name",
            "modified gas generator",
        ),
        (
            RegenerativeJacketSpec,
            _valid_regenerative_jacket_spec_kwargs,
            "name",
            "modified jacket",
        ),
    ],
)
def test_specs_are_frozen(spec_class, kwargs_builder, field_name, new_value):
    """Specs must be immutable so simulations cannot mutate shared configurations."""
    spec = spec_class(**kwargs_builder())

    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(spec, field_name, new_value)
