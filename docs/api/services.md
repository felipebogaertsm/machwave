# services

External service integrations, I/O helpers, and visualization tools.

- **CEA** — Wrapper around NASA CEA (via RocketCEA) for thermochemical equilibrium calculations: adiabatic flame temperature, exhaust molecular weight, γ, Isp (frozen and shifting), and condensed-phase species fractions (`cea` extra).
- **eng** — `.eng` thrust-curve file generation for OpenRocket, RASAero, and other flight simulators.
- **plots** — Plotly-based interactive charts for internal ballistics results, Monte Carlo histograms/CDFs, and trajectory profiles (`plots` extra).

See [eng](services/eng.md) for the `.eng` writer and [plots](services/plots.md) for the visualization API.

::: machwave.services
