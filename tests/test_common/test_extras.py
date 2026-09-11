import json

import pytest

import machwave.common.extras as extras

ALL_EXTRAS = [
    extras.CEA,
    extras.LIQUID,
    extras.FMM,
    extras.PLOTS,
    extras.ROCKETPY,
]


def test_require_returns_an_installed_module():
    assert extras.require("json", extras.FMM) is json


def test_require_returns_the_named_submodule():
    assert extras.require("json.decoder", extras.FMM).__name__ == "json.decoder"


def test_require_raises_for_a_missing_package():
    with pytest.raises(extras.MissingOptionalDependencyError) as exc_info:
        extras.require("machwave_absent_dependency", extras.FMM)

    message = str(exc_info.value)

    assert "Non-BATES grain geometries" in message
    assert "`machwave_absent_dependency`" in message
    assert "pip install machwave[fmm]" in message


def test_require_chains_the_original_import_error():
    with pytest.raises(extras.MissingOptionalDependencyError) as exc_info:
        extras.require("machwave_absent_dependency", extras.FMM)

    assert isinstance(exc_info.value.__cause__, ImportError)


def test_missing_optional_dependency_error_is_an_import_error():
    assert issubclass(extras.MissingOptionalDependencyError, ImportError)


def test_missing_optional_dependency_error_exposes_the_extra():
    assert (
        extras.MissingOptionalDependencyError("skfmm", extras.FMM).extra == extras.FMM
    )


@pytest.mark.parametrize(
    "module_name, expected_distribution",
    [
        ("CoolProp.CoolProp", "coolprop"),
        ("skfmm", "scikit-fmm"),
        ("skimage.measure", "scikit-image"),
        ("trimesh", "trimesh"),
        ("rocketcea.cea_obj", "rocketcea"),
        ("plotly.graph_objects", "plotly"),
    ],
)
def test_error_names_the_distribution_not_the_import_name(
    module_name, expected_distribution
):
    error = extras.MissingOptionalDependencyError(module_name, extras.FMM)

    assert f"`{expected_distribution}` package" in str(error)


def test_feature_overrides_the_default_wording():
    error = extras.MissingOptionalDependencyError(
        "trimesh", extras.FMM, "STL grain segments"
    )

    assert str(error).startswith("STL grain segments require the `trimesh` package")
    assert "pip install machwave[fmm]" in str(error)


@pytest.mark.parametrize("extra", ALL_EXTRAS)
def test_every_extra_has_default_wording(extra):
    assert str(extras.MissingOptionalDependencyError("package", extra)).endswith(
        f"Install it with `pip install machwave[{extra}]`."
    )
