#!/usr/bin/env zsh
set -euo pipefail

# Packages you want diagrams for
MODULES=(
  machwave
  machwave.models.grain
  machwave.models.thrust_chamber
  machwave.models.motors
  machwave.models.propellants
  machwave.simulation
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
