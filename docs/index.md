# Machwave

Machwave is an open source Python library for chemical rocket propulsion simulation. The
library enables modeling and simulating solid (liquid and hybrid coming soon) rocket
motors and engines.

## Why Machwave?

Machwave provides a programmatic interface for modeling chemical propulsion systems, 
allowing users to have more control and flexibility over their designs and simulations.
Other tools may offer similar capabilities, but they often come with limitations such as
being closed source, lacking integration with trajectory simulations, or not being
flexible enough for more advanced users.

Machwave:

- Is open source and free to use.
- Enables easy interation with internal and 3rd party trajectory simulation libraries.
- Allows for unlimited customization and control over the modeling process.
- Facilitates version control and collaboration through its programmatic interface.

This makes it perfect for students, researchers, and engineers working on preliminary
designs.

## Installation

```bash
pip install machwave
```

or, for the full integration with RocketPy:

```bash
pip install machwave[rocketpy]
```

## Examples

You can find examples of how to use Machwave in the 
[examples directory](https://github.com/felipebogaertsm/machwave/tree/main/examples).


## Development Setup

If you're contributing to Machwave, you'll need [Poetry](https://python-poetry.org/) for dependency management.

```bash
git clone https://github.com/felipebogaertsm/machwave.git
cd machwave
poetry install
```