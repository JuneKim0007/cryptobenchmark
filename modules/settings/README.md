# settings

The harness key table, shared by config, preparation and benchmark. Each YAML setting is one `Key`:
how it is read, validated, written and merged. A `Section` is an ordered table of keys; reading rejects
an unknown key, writing emits only what is set, merging is key by key.

| File | Responsibility |
|---|---|
| `Key.kt` | one setting: read, get, with, write, merge; a nested key holds a section |
| `Section.kt` | read (unknown key → `unknown_keys`), write, merge for a table of keys |
| `Values.kt` | typed reads of one value: bounded int, choice; failures name the key |
| `Harness.kt` | `HarnessSettings`, `EnergySettings`, `CpuRequest` with their key tables |
| `Facts.kt` | what the device can support, read from `discovery/facts.yaml`; unknown when not gathered |
| `Support.kt` | `Supported` / `NotSupported(reason)`, and `Unsupported(path, reason, required)` for a set key |

Depends on nothing; the module-isolation check allows it on every module's classpath that reads a harness.
Add a setting: one `Key` in the table and one field on the typed class.

## Device support

A key may declare `requires(value, facts)`. When `effective.yaml` is built, every set key is checked
against the device's facts:

| Not supported, and | Set in `run.harness` | Set by a test-set rule |
|---|---|---|
| not required | removed, warning `not_supported: <path>: <reason>` | removed from those entries, same warning |
| `required: true` | the config fails with that reason | those entries are skipped with that reason |

`cpu: {core: <index> | big, required: <bool>}` pins the measuring thread to one core. It needs the
native affinity library in the installed APK (`facts.pinning`) and an online core; without facts
(a host run) it is `facts_unknown`. Other processes can still run on that core: pinning is not
isolation, which needs root.
