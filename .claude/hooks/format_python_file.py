"""Format and lint the Python file an agent just edited, reporting lint failures back."""

import json
import pathlib
import subprocess
import sys

LINT_FAILURE_EXIT_CODE = 2


def main() -> int:
    hook_input = json.load(sys.stdin)
    file_path = pathlib.Path(hook_input.get("tool_input", {}).get("file_path", ""))
    if file_path.suffix != ".py" or not file_path.is_file():
        return 0

    ruff = [sys.executable, "-m", "ruff"]
    subprocess.run([*ruff, "format", "--quiet", str(file_path)], check=False)
    lint = subprocess.run(
        [*ruff, "check", "--fix", "--quiet", str(file_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if lint.returncode != 0:
        print(lint.stdout + lint.stderr, file=sys.stderr)
        return LINT_FAILURE_EXIT_CODE
    return 0


if __name__ == "__main__":
    sys.exit(main())
