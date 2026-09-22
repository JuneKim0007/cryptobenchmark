#!/usr/bin/env bash
# One command for a live run: warms the build, then runs the whole pipeline into results/demo.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
config="$root/config/global-quick.yaml"
results="$root/results/demo"
discovery=overwrite
warm_only=no

while [ $# -gt 0 ]; do
  case "$1" in
    --warm) warm_only=yes ;;
    --fast) config="$root/config/global-demo.yaml" ;;
    --reuse) discovery=reuse ;;
    --config) shift; config="$1" ;;
    --results) shift; results="$1" ;;
    -h|--help)
      echo "usage: scripts/demo.sh [--warm] [--fast] [--reuse] [--config FILE] [--results DIR]"
      echo "  --warm    compile both tools and exit, so the live run has nothing to build"
      echo "  --fast    three primitives, one input size (about 8s) instead of eleven (about 30s)"
      echo "  --reuse   keep this device's capture instead of probing again"
      exit 0 ;;
    *) echo "usage: scripts/demo.sh [--warm] [--fast] [--reuse] [--config FILE] [--results DIR]" >&2; exit 2 ;;
  esac
  shift
done

banner() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

if [ "$warm_only" = yes ]; then
  banner "build"
  "$root/tools/jca-contract/gradlew" -p "$root/tools/jca-contract" classes -q --no-daemon
  "$root/tools/jca-contract/gradlew" -p "$root/tools/quick-bench" classes -q --no-daemon
  banner "ready"
  echo "both tools compiled; run: scripts/demo.sh"
  exit 0
fi

banner "run"
if [ "$discovery" = overwrite ]; then rm -rf "$results"; fi
python3 "$root/scripts/pipeline.py" --config "$config" --results "$results" --discovery "$discovery" --bench --stream

banner "result"
head -12 "$results/analysis/summary.md"
echo "..."
echo
echo "$(( $(wc -l < "$results/analysis/summary.md") - 2 )) cases in $results/analysis/summary.md"
ls "$results/analysis"
