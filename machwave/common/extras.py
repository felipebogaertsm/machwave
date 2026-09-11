"""
Resolution of the optional dependencies behind Machwave's packaging extras.

Modules reached only once a feature is used guard their own import at module
level and re-raise `MissingOptionalDependencyError`; that keeps the third-party
names real and fully typed. `require` is for modules on the import path, which
must stay importable without their dependency. It returns the module untyped,
so prefer the module-level guard wherever both work.
"""

import importlib
import types

CEA = "cea"
LIQUID = "liquid"
FMM = "fmm"
PLOTS = "plots"
ROCKETPY = "rocketpy"

# Default wording per extra, as a plural noun phrase, so that the message reads
# "<feature> require the `<distribution>` package".
_FEATURE_BY_EXTRA = {
    CEA: "Thermochemical properties computed from propellant composition",
    LIQUID: "Tank and injector fluid properties",
    FMM: "Non-BATES grain geometries",
    PLOTS: "Machwave's built-in plots",
    ROCKETPY: "RocketPy adapters",
}

# Import name to distribution name, where the two differ.
_DISTRIBUTION_BY_MODULE = {
    "CoolProp": "coolprop",
    "skfmm": "scikit-fmm",
    "skimage": "scikit-image",
}


class MissingOptionalDependencyError(ImportError):
    """Raised when a feature needs an optional dependency that is not installed."""

    def __init__(
        self, module_name: str, extra: str, feature: str | None = None
    ) -> None:
        """
        Build the error from the missing dependency and the extra that ships it.

        Args:
            module_name: Import name of the package, e.g. `skimage.measure`.
            extra: Packaging extra that installs it.
            feature: Plural noun phrase naming the feature, overriding the default
                wording for `extra`. Use it when one extra gates more than one
                feature.
        """
        top_level = module_name.partition(".")[0]
        distribution = _DISTRIBUTION_BY_MODULE.get(top_level, top_level)
        feature = feature or _FEATURE_BY_EXTRA[extra]

        self.extra = extra

        super().__init__(
            f"{feature} require the `{distribution}` package. "
            f"Install it with `pip install machwave[{extra}]`."
        )


def require(
    module_name: str, extra: str, feature: str | None = None
) -> types.ModuleType:
    """
    Import an optional dependency, naming the extra that ships it on failure.

    Args:
        module_name: Import name of the package, e.g. `skimage.measure`.
        extra: Packaging extra that installs it.
        feature: Plural noun phrase naming the feature, overriding the default
            wording for `extra`.

    Returns:
        The imported module.

    Raises:
        MissingOptionalDependencyError: If the package is not installed.
    """
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        raise MissingOptionalDependencyError(module_name, extra, feature) from e
