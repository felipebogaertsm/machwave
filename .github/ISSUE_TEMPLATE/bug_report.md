---
name: Bug report
about: Report a defect in Machwave
title: ""
labels: bug
assignees: ""
---

## Description

A clear description of what the bug is.

## Reproduction steps

Minimal steps to reproduce the behaviour. A short Python snippet is ideal:

```python
# paste minimal repro here
```

## Expected behaviour

What you expected to happen.

## Actual behaviour

What actually happened. Include the full traceback if there is one.

## Simulation context

If the bug surfaces in a simulation, please describe what was being modelled:

- Engine type: solid motor / biliquid engine / hybrid / other
- Feed system (if biliquid): pressure-fed / pump-fed / stacked tank / other
- Grain geometry (if solid): BATES / star / finocyl / custom / other
- Propellant: name or composition
- Relevant simulation parameters: time step, chamber pressure, mixture ratio, etc.

## Environment

- Machwave version: (output of `python -c "import machwave; print(machwave.__version__)"`)
- Python version:
- Operating system and version:
- Installation method: `pip install machwave` / editable install from source / other

## Additional context

Logs, screenshots, plots, or links that help diagnose the issue.
