import os
import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).parents[2] / "examples"

_TOP_LEVEL = sorted(_EXAMPLES_DIR.glob("*.py"))
_LOSSES = sorted((_EXAMPLES_DIR / "losses").glob("*.py"))
_ALL_SCRIPTS = _TOP_LEVEL + _LOSSES

# Patch plotly's show() to a no-op before running the script so that
# headless environments (CI, no IPython) don't raise on fig.show() calls.
_PREAMBLE = (
    "import os, plotly.basedatatypes as _b, runpy; "
    "_b.BaseFigure.show = lambda *a, **kw: None; "
    "runpy.run_path(os.environ['_SMOKE_SCRIPT'], run_name='__main__')"
)


def _script_id(script: Path) -> str:
    return str(script.relative_to(_EXAMPLES_DIR))


@pytest.mark.smoke
@pytest.mark.parametrize(
    "script", _ALL_SCRIPTS, ids=[_script_id(s) for s in _ALL_SCRIPTS]
)
def test_example_runs(script: Path) -> None:
    env = {**os.environ, "_SMOKE_SCRIPT": str(script)}
    result = subprocess.run(
        [sys.executable, "-c", _PREAMBLE],
        env=env,
        timeout=600,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Example '{_script_id(script)}' exited with code {result.returncode}.\n"
        f"--- stderr ---\n{result.stderr}\n"
        f"--- stdout ---\n{result.stdout}"
    )
