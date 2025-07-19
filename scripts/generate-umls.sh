#!/usr/bin/env zsh
set -euo pipefail

# Packages you want diagrams for
MODULES=(
  machwave.models.propulsion.grain
  machwave.models.propulsion.grain.fmm
)

OUT_DIR=docs/umls
mkdir -p "$OUT_DIR"

for module in "${MODULES[@]}"; do
  out="$OUT_DIR/${module//./_}.puml"   # dots → underscores
  echo "Generating $out …"
  poetry run py2puml machwave "$module" > "$out"
done

echo "✅ UML diagrams generated"
