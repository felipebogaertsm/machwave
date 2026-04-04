#!/usr/bin/env zsh
set -euo pipefail

# Packages you want diagrams for
MODULES=(
  machwave
  machwave.models.propulsion
  machwave.models.propulsion.grain
  machwave.models.propulsion.thrust_chamber
  machwave.models.propulsion.motors
  machwave.models.propulsion.propellants
  machwave.simulations
  machwave.states
)

OUT_DIR=docs/umls
mkdir -p "$OUT_DIR"

for module in "${MODULES[@]}"; do
  out="$OUT_DIR/${module//./_}.puml"
  echo "Generating $out …"
  uv run py2puml ${module//.//} $module > $out
done

echo "UML diagrams generated"
