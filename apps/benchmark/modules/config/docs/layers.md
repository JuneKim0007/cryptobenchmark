# layers

A global file with `layers: [base.yaml, overlays/energy.yaml]` is a composition (`layers/LayerStack.kt`): each listed file, lowest first, then the composition's own keys, merged into one global.yaml before its parser runs.

| rule | value |
|---|---|
| merge | mappings by key; lists and scalars replace; `run.passes` replaces whole (`MERGE_RULES`) |
| paths | layers and `selection.testSet` relative to the composition unless absolute |
| `schemaVersion` | required on the composition; a layer may omit it, else it must match |
| refused | a layer that lists `layers` (`nested_layers`), a missing layer (`missing_file`), `layers` not a non-empty list |
| an unknown key | its message ends with the layer that wrote it, `(layer N <file>)` |
| provenance | `generatedFrom.layers` and `generatedFrom.settings` in effective.yaml ([generated.md](generated.md)) |

A file without `layers` is a stack of one. The pipeline refuses a composition as `--config` (`not_supported: ... lists layers`): its input digest, bundled providers, known vectors and dependency check read the authored file raw.
