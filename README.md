# Machwave

Machwave is a Python library for chemical propulsion simulation. The library makes it
easy to model solid or liquid rocket engines, analyse performance and integrate the
results into trajectory simulations.

## Getting Started

### Installation

Install Machwave using pip:

```bash
pip install machwave
```

### Documentation

The full documentation is available at
[felipebogaertsm.github.io/machwave](http://felipebogaertsm.github.io/machwave/).

### Development Setup

If you're contributing to Machwave, you'll need [Poetry](https://python-poetry.org/) for dependency management.

#### Installing Poetry

**macOS / Linux / Ubuntu:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell):**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

After installation, verify it worked:

```bash
poetry --version
```

For more details, visit the [official Poetry installation guide](https://python-poetry.org/docs/#installation).

#### Clone and Install

Clone the repository and install dependencies:

```bash
git clone https://github.com/felipebogaertsm/machwave.git
cd machwave
make install
```

#### Publishing a New Release

1. **Bump the version** with Poetry:

   ```bash
   poetry version patch   # or minor / major
   ```

2. **Commit and push** the version bump:

   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to $(poetry version -s)"
   git push
   ```

   This triggers the CI pipeline (lint > test > docs deploy). Ensure it passes.

3. **Trigger the publish workflow** on GitHub:
   Go to **Actions → "Publish Machwave to PyPI" → Run workflow**.

   The workflow builds the package with `poetry build` and publishes it to PyPI using the `MACHWAVE_PUBLISHING_TOKEN` secret stored in the `publish` GitHub environment.
