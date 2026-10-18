# settings

The harness key table, shared by config, preparation and benchmark. Each YAML setting is one `Key`:
how it is read, validated, written and merged. A `Section` is an ordered table of keys; reading rejects
an unknown key, writing emits only what is set, merging is key by key.

| File | Responsibility |
|---|---|
| `Key.kt` | one setting: a `Leaf` holds a value, a `Nested` holds a section merged key by key, with an optional `requires` and `resolve` |
| `Section.kt` | read (unknown key → `unknown_keys`), write, merge, and `forDevice`: what the device can run and what it cannot |
| `Values.kt` | type checks of one value; bounds and choices are checked once, by the class the value goes into |
| `Harness.kt` | `HarnessSettings`, `EnergySettings`, `CpuSettings` with their key tables |
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

`cpu: {core: <index> | big, required: <bool>}` pins the measuring thread to one core. It merges field by
field, so a rule naming only `core` keeps the run's `required`. It needs the native affinity library in
the installed APK (`facts.pinning`) and an online core; `big` is resolved here, once, to the online core
with the highest `cpuinfo_max_freq`, so the device only ever pins an index. Without facts it is
`facts_unknown`. An entry is checked with the run values it inherits; when its own value is dropped the
warning ends `; run.harness.cpu applies`. Pinning restricts our thread; it is not isolation, which needs root.
