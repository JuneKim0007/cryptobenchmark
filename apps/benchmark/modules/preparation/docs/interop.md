# interop

`InteropOracle.check(pair)`: whether two members of one perf-repair group interoperate. `InteropRun.run(capability, plan, capture, out)` checks every plan pair and writes `interop.yaml`. perf-repair's guide runs it after grouping, before options. Code under `src/main/kotlin/interop/`; covered by `InteropOracleTest`, `InteropFileGoldenTest`.

## Diagram

```mermaid
flowchart LR
    G[perf-repair groups.json] -- interop-plan --> P[interop_plan.yaml]
    P -- pipeline.py --bench --interop --> H[InteropKt on the host JVM]
    P -- pipeline.py --device --interop --> D[InteropCheck on the device]
    H --> R[results/device_id/interop/interop.yaml]
    D --> R
    R -- interop-read --> X[perf-repair grouping/interop.yaml, groups.json interop]
```

## Check

| rule | value |
|---|---|
| member unavailable | both directions `not_checkable`, `not_registered: ...`; mode `none` |
| direction | the first member's provider runs the type's first timed operation once (`engine-operations.yaml`), the other member consumes it through the peer engine (`apps/benchmark/modules/preparation/docs/peer.md`), under its own algorithm name |
| mode | the row's: `produce_consume` for ciphers, signatures and generated keys; `same_output` for digests, MACs and agreements; `none` without a row |
| key | one key per direction, planned and generated for the producer; its generator the producer's provider, else the first provider in precedence order that has one; the consumer rebuilds it from its encoding |
| parameters | each member at its own defaults; only IV and GCM parameters travel with the ciphertext |
| pair cases | seed 0; input size default 16 |
| no key | `not_checkable` `no_key`, `key_generation_failed` |
| verdicts | the peer engine's: the producer failing is `producer_failed`; the rest as its outcomes table |
| pair result | `fail` when a direction fails; `pass` when both pass; `not_checkable` otherwise |

## interop_plan.yaml

Schema `interop_plan` v1, written by perf-repair (`apps/perf-repair/docs/grouping.md`).

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
