# services.plots

Interactive Plotly-based visualization for simulation results.

!!! note "Requires the `plots` extra"
    `pip install machwave[plots]`. Importing any module below without it raises an `ImportError` naming that command.

- **Internal ballistics** — Dual-axis thrust vs. chamber pressure plot, per-segment mass flux over time.
- **Biliquid engine profiles** — Tank pressure and propellant mass traces for oxidizer and fuel.
- **Ballistics** — Altitude, velocity, and acceleration subplots for trajectory analysis.
- **Monte Carlo** — Histograms (with optional KDE overlay), CDF plots with configurable percentile markers, for any scalar result property across simulation scenarios.

All functions return Plotly `Figure` objects that can be displayed inline or exported.

::: machwave.services.plots
