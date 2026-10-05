# config

Authored, committed. Nothing here is generated.

| File | Holds |
|---|---|
| `global.yaml` | the four settings most runs change: test set, input sizes, seed, iterations. Everything else takes its default |
| `global.reference.yaml` | every key `global.yaml` accepts, with its default and whether it is required. Not read by anything |
| `global-quick.yaml` | the same, pointed at `testsets/quick.yaml` |
| `global-demo.yaml` | `testsets/smoke.yaml`, one input size — the live demo |
| `testsets/scope.yaml` | README scope with explicit key sizes and parameters |
| `testsets/quick.yaml` | one representative per primitive in scope |
| `testsets/all.yaml` | everything the device can run |
| `testsets/smoke.yaml` | three staples |

Generated from these plus the probe: `results/configuration/inventory.yaml`, `results/configuration/effective.yaml`, and beside it `report.yaml` (warnings and skips).
Fields and precedence: `modules/config/docs/config.md`. What a run resolved to, and which file each value came from: `python scripts/explain.py`.
