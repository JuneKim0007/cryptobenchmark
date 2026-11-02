# interop

`InteropOracle.check(pair)`: whether two members of one perf-repair group interoperate. `InteropRun.run(capability, plan, capture, out)` checks every plan pair and writes `interop.yaml`. Code under `src/main/kotlin/interop/`; covered by `InteropOracleTest`.

## Diagram

```mermaid
flowchart LR
    G[perf-repair groups.json] -- interop-plan --> P[interop_plan.yaml]
    P -- pipeline.py --bench --interop --> H[InteropKt on the host JVM]
    P -- pipeline.py --device --interop --> D[InteropCheck on the device]
    H --> R[results/interop/interop.yaml]
    D --> R
    R -- interop-read --> X[perf-repair grouping/interop.yaml, groups.json interop]
```

## Check

| rule | value |
|---|---|
| member unavailable | both directions `not_checkable`, `not_registered: ...`; mode `none` |
| mode `produce_consume` | the type has an artifact-consuming operation (DECRYPT, VERIFY): A produces, B consumes, then B produces, A consumes |
| mode `same_output` | otherwise: both outputs for the same key and input compared |
| key | one key per direction, planned and generated for the producer, shared by both sides |
| parameters | each member at its own defaults; only IV and GCM parameters travel with the ciphertext |
| pair cases | seed 0; input size default 16 |
| `not_checkable` | `InvalidKeyException`, `InvalidAlgorithmParameterException`, `ClassCastException` (`key_or_parameters_rejected`); producer failure; no key; outputs not byte arrays |
| `fail` | `BadPaddingException`, `IllegalBlockSizeException`, `SignatureException`, `verify_failed`, other bytes returned, outputs differ |
| pair result | `fail` when a direction fails; `pass` when both pass; `not_checkable` otherwise |

## interop_plan.yaml

Schema `interop_plan` v1, written by perf-repair (`perf-repair/docs/grouping.md`).

| key | rule |
|---|---|
| `pairs[]` | `{id, group, a, b, keySize?, inputSize?}`; ids unique |
| `notCheckable[]` | perf-repair's own record of pairs it holds back; this module does not read it |
| `a`, `b` | `{type, algorithm, provider}`; same type |

## interop.yaml

| key | holds |
|---|---|
| `schemaVersion` | `1` |
| `generatedFrom` | `plan`, `capture` file names |
| `pairs[]` | `{id, group, a, b, result, mode, directions: {aToB, bToA}, reason}`; `a`, `b` as in the plan |
| `result`, direction labels | `pass`, `fail`, `not_checkable` |
| `reason` | `aToB: ...; bToA: ...` for each direction that did not pass; empty on `pass` |
