# <prepare>

`effective.yaml` → prepared cases. Nothing here runs inside a measurement.

## Flow

```
effective.yaml ─► InboundFile ─► GlobalReader ─► PrimitiveReader ─► BenchmarkRequest
                                                                        │
                        DiscoveryCapability (capture + trial) ─► CaseResolver ─► cases + rejections
                                                                        │
                            KeyPlanner ─► KeyMaterialGenerator ─► InputPreparer ─► CaseCheck ─► PreparedRun
```

Each stage takes the previous stage's value, so the order is checked by the compiler.

## Axes of one case

| Axis | From | Absent means |
|---|---|---|
| operation | `AxisRules` per engine type; `operations` in the entry narrows it | every operation of the type |
| key size | entry `keySizes`; a size written into the name (`AES_128`) | the provider's default |
| input size | entry `inputSizes`, else `run.inputSizes` | the type takes no input |
| phase | `run.phases` | — |
| parameters | entry `key` and `parameters` trees | the provider fills them in |

## Parameter trees

`{class, arguments}` by fully qualified name; an argument is a literal, `fresh(n)`, `{field: Class.NAME}`, or another tree.
Only subtypes of `AlgorithmParameterSpec`, `PSource` and `BigInteger` may be named. A failure names its path.

## Failures

| Reason | Stage |
|---|---|
| `provider_not_installed`, `not_registered`, `transformation_fails`, `not_tried` | resolve |
| `bind_failed: <path>`, `key_parameters_and_key_sizes`, `unsupported_operation` | resolve |
| `no_key_generator`, `key_generation_failed` | key |
| `input_preparation_failed`, `dry_run_failed` | input, check |

`policy.onFailure` decides: `skip` records each in `results/preparation/skipped.yaml`, `stop` writes the report and exits.

## Limits

- one call per case proves it runs; it says nothing about timing
- keys are reused across cases with the same recipe
- `fresh(n)` specs must be drawn before the timer; `BoundParameters.varies` says when
- `KeyInitializer` has one implementation on the host; the per-provider slot is for AndroidKeyStore
  and StrongBox, which generate keys through their own spec types (#33)
