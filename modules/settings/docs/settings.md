# settings

The harness key table read by config, preparation and benchmark. Each YAML setting is one `Key`; a `Section` is an ordered table of keys. File map: [index.md](index.md).

## Harness keys

All keys are unset by default (null, empty `energy`).

| key | value |
|---|---|
| `iterations` | int `>= 1` |
| `warmupIterations` | int `>= 1`; below 1: `not_supported: warmupIterations <n>, androidx needs at least 1; leave it out to let the library decide` |
| `profiling` | `none`, `MethodTracing`, `StackSampling` |
| `energy.capture` | `none`, `measured`, `dry` |
| `energy.windowSeconds` | int `>= 1` |
| `energy.warmupSeconds` | int `>= 1` |
| `energy.cooldownSeconds` | int `>= 0` |
| `energy.source` | `rails`, `manafa`; unset means `rails` |
| `cpu.core` | core index `0..63` or `big`, as a number or a word |
| `cpu.required` | bool |

Energy semantics: `docs/energy.md`.

## Section rules

| operation | rule |
|---|---|
| read | null document = empty; null value = unset |
| unknown key | `unknown_keys: <path> [..], known [..]` |
| leaf error | suffixed `at <path>` |
| write | only set keys; an empty `energy` is not written |
| merge | `Leaf`: the later value replaces; `Nested` (`energy`, `cpu`): key by key |
| `forDevice` | returns (honoured value, unsupported list); an unsupported nested block is removed whole |

| value error | text |
|---|---|
| wrong type | `wrong_type: <label> expects <a number\|true or false\|text\|a number or a word>, got <Class>` |
| YAML boolean in a text key | `invalid: <label> <v> (YAML reads off/on/yes/no as booleans), write one of [..]` |
| unsupported | `not_supported: <path>: <reason>`, plus ` (required)` when required |

A new setting is one `Key` in the table and one field on the typed class.

## Device support

Only `cpu` declares `requires` and `resolve`. How config applies the result: `modules/config/docs/generated.md#device-support`.

`cpu` checks run in this order; the first failing one is the reason.

| condition | reason |
|---|---|
| `core` unset | `no_core: cpu.core is not set` |
| `pinning` fact missing | `facts_unknown` for `pinning` |
| `pinning` false | `no_pinning: the installed app carries no native affinity library` |
| `cpu.cores` fact missing | `facts_unknown` for `cpu.cores` |
| `big` and no online core has `maxKhz` | `no_frequencies: no online core reports a maximum frequency` |
| index not an online core | `no_core: core <n> is not an online core of [..]` |

`cpu.core` outside `0..63` and not `big` fails `invalid: cpu.core <v>, an index 0..63 or big`.

`run.metrics` (`Metric`): config refuses an unsupported metric, `not_supported: run.metrics.<M>: <reason>`; never dropped. It selects what `benchmark.json` reports, not what androidx runs: ALLOCATION not requested: androidx still runs its allocation phase; it is not reported. `CPU_EVENTS` also turns androidx's counter on: `modules/android/docs/harness.md#cryptobenchmark`.

| metric | condition | reason |
|---|---|---|
| `TIME`, `ALLOCATION` | always supported | |
| `CPU_EVENTS` | `rooted` fact missing | `facts_unknown` for `rooted` |
| `CPU_EVENTS` | `rooted` false | `no_root: CPU event counters need a rooted device` |

| `Metric.read` input | failure |
|---|---|
| unknown name | `invalid: <path> <name>, known [TIME, ALLOCATION, CPU_EVENTS]` |
| repeated name | `duplicate: <path> [..]` |
| no `TIME` | `missing_metric: <path> [..], TIME is always measured` |

| rule | value |
|---|---|
| `big` | resolves to the online core with the highest `maxKhz`; highest index on a tie |
| device | pins only a resolved index; pinning: `modules/android/docs/harness.md#core-pinning` |
| no facts file | `facts_unknown: no facts.yaml for this run` |
| fact missing | `facts_unknown: facts.yaml has no <fact>` |

## facts.yaml

Written by `scripts/device/facts.py` into the discovery directory.

| field | value |
|---|---|
| `schemaVersion` | `1`; other: `unsupported: facts.yaml schemaVersion <v>` |
| `os.sdkInt` | int |
| `rooted` | bool |
| `cpu.cores[]` | `{core, online, maxKhz}`; `maxKhz` = `cpuinfo_max_freq` |
| `pinning` | APK contains `lib/<abi>/libaffinity.so` |

Wrong types fail `wrong_type: facts.yaml <field> expects ...`.

## Dependencies

`:settings` depends on no project or library (JUnit for tests). Module-isolation puts its sources on every module except discovery. Dependency table: `docs/architecture.md`.
