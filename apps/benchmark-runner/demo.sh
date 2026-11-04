#!/usr/bin/env bash
# One command for a live run: warms the build, then runs the whole pipeline into results/demo/<device_id>.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
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
      echo "usage: apps/benchmark-runner/demo.sh [--warm] [--fast] [--reuse] [--config FILE] [--results DIR]"
      echo "  --warm    compile the benchmark CLI and exit, so the live run has nothing to build"
      echo "  --fast    three primitives, one input size (about 8s) instead of eleven (about 30s)"
      echo "  --reuse   keep this device's capture instead of probing again"
      exit 0 ;;
    *) echo "usage: apps/benchmark-runner/demo.sh [--warm] [--fast] [--reuse] [--config FILE] [--results DIR]" >&2; exit 2 ;;
  esac
  shift
done

banner() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

if [ "$warm_only" = yes ]; then
  banner "build"
  "$root/apps/benchmark/gradlew" -p "$root/apps/benchmark/cli" classes -q --no-daemon
  banner "ready"
  echo "the benchmark CLI compiled; run: apps/benchmark-runner/demo.sh"
  exit 0
fi

banner "run"
python3 "$root/apps/benchmark-runner/pipeline.py" --config "$config" --results "$results" --discovery "$discovery" --bench --stream

banner "result"
# newest manifest: the folder this run just finished; the root may hold other devices
device="$(dirname "$(ls -t "$results"/*/manifest.yaml | head -1)")"
head -12 "$device/analysis/summary.md"
echo "..."
echo
echo "$(( $(wc -l < "$device/analysis/summary.md") - 2 )) cases in $device/analysis/summary.md"
ls "$device/analysis"
