# settings

The harness key table, shared by config, preparation and benchmark. Each YAML setting is one `Key`:
how it is read, validated, written and merged. A `Section` is an ordered table of keys; reading rejects
an unknown key, writing emits only what is set, merging is key by key.

| File | Responsibility |
|---|---|
| `Key.kt` | one setting: read, get, with, write, merge; a nested key holds a section |
| `Section.kt` | read (unknown key → `unknown_keys`), write, merge for a table of keys |
| `Values.kt` | typed reads of one value: bounded int, choice; failures name the key |
| `Harness.kt` | `HarnessSettings` and `EnergySettings` with their key tables |

Depends on nothing; the module-isolation check allows it on every module's classpath that reads a harness.
Add a setting: one `Key` in the table and one field on the typed class.
