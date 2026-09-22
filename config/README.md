# config

Authored, committed. Nothing here is generated.

| File | Holds |
|---|---|
| `global.yaml` | `selection` (test set, extra excludes), `run`, `policy` |
| `global-quick.yaml` | the same, pointed at `testsets/quick.yaml` |
| `global-demo.yaml` | `testsets/smoke.yaml`, one input size — the live demo |
| `testsets/scope.yaml` | README scope with explicit key sizes and parameters |
| `testsets/quick.yaml` | one representative per primitive in scope |
| `testsets/all.yaml` | everything the device can run |
| `testsets/smoke.yaml` | three staples |

Generated from these plus the probe: `results/configuration/inventory.yaml`, `results/configuration/effective.yaml`.
Fields and precedence: `modules/config/docs/config.md`.
