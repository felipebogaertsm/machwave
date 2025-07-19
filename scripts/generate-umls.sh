#!/usr/bin/env zsh
set -euo pipefail

# Packages you want diagrams for
MODULES=(
  machwave
  machwave.models.propulsion
  machwave.models.propulsion.grain
  machwave.montecarlo
)

OUT_DIR=docs/umls
mkdir -p "$OUT_DIR"

for module in "${MODULES[@]}"; do
  out="$OUT_DIR/${module//./_}.puml"
  echo "Generating $out …"
  poetry run py2puml ${module//.//} $module > $out
done

echo "UML diagrams generated"
