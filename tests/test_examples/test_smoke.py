import os
import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).parents[2] / "examples"

_TOP_LEVEL = sorted(_EXAMPLES_DIR.glob("*.py"))
_LOSSES = sorted((_EXAMPLES_DIR / "losses").glob("*.py"))
_ALL_SCRIPTS = _TOP_LEVEL + _LOSSES


def _script_id(script: Path) -> str:
    return str(script.relative_to(_EXAMPLES_DIR))


@pytest.mark.parametrize(
    "script", _ALL_SCRIPTS, ids=[_script_id(s) for s in _ALL_SCRIPTS]
)
def test_example_runs(script: Path) -> None:
    env = {**os.environ, "PLOTLY_RENDERER": "json"}
    result = subprocess.run(
        [sys.executable, str(script)],
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
