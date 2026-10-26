# generated

`inventory.yaml` (what the device has) and `effective.yaml` (what will run), written by `Configuration(output)` into `output`. Pipeline output directory: `docs/results.md`. Authored inputs: [config.md](config.md).

## Flow

```
probe_<utc>.yaml + trial_<utc>.yaml -> InventoryBuilder -> inventory.yaml
global.yaml -> selection.testSet -> testsets/<name>.yaml -+
inventory.yaml + facts.yaml (optional) --------------------+-> EffectiveBuilder -> effective.yaml
```

| call | does |
|---|---|
| `inventory(captureFile, trialFile)` | deletes the old inventory; reads capture (schema 1) and trial (schema 2); writes inventory |
| `effective(globalFile, inventoryFile, factsFile?)` | deletes the old effective; reads global and its test set; writes effective |
| `readEffective()` | reads `effective.yaml` back |

Host entry `ConfigureKt`: `docs/tools.md`.

## inventory.yaml

| rule | value |
|---|---|
| entries | one per trial default run, service and transformation; trial entries without `defaultRun` are left out |
| provider order | capture precedence, then providers seen only in the trial |
| entry fields | `runs`, `keySizes`, `inputSizes`, `keyAlgorithm`, `keyProvider`, `providerChose`, `bareName`, `reason`; empty ones omitted |
| `inputSizes` | recorded only when the run's input size differs from the trial's `defaultRunInputSize` |
| `reason` | trial error, else `failed` |
| `generatedFrom` | `capture`, `trial` file names; `device` = the capture's `runtime` block |
| duplicate | names differing only by case in one provider and type: `duplicate_name` |
| pairing | capture and trial `capturedAtMillis` differ: `mismatched_trial: capture <a>, trial <b>` |

## Build order

| step | rule |
|---|---|
| select | include (empty = all), then drop anything matching a test-set or global exclude |
| skip | include matching nothing: `no_match: nothing on this device matches the include`; selected with `runs: false`: `not_runnable: <reason>` |
| stop check | under `stop`, any skip fails `stopped_on_failure: <n>` listing the skips |
| resolve | overrides per entry, by precedence in [config.md](config.md#override-precedence) |
| device check | run and entry harness against facts |
| stop check | repeated after the device check |
| empty | nothing selected: `nothing_selected` |

Skips have stage `config`.

## Device support

Facts come from `facts.yaml` (`--facts=`); without it every key that needs a fact is `facts_unknown`. Key rules: `modules/settings/docs/settings.md`.

| unsupported, and | set in `run.harness` | set by an override |
|---|---|---|
| not required | removed; warning `not_supported: <path>: <reason>` | removed from that entry; same warning |
| `required: true` | config fails (`IllegalArgumentException`), whatever `onFailure` | entry skipped; governed by `onFailure` |

An entry is checked as `run.harness` merged with its own harness. When the run sets the dropped key, the warning ends `; run.harness.<key> applies`.

## Entry values

| key | value |
|---|---|
| `keySizes` | override value, else empty |
| `inputSizes` | override value, else the inventory's observed `inputSizes` |
| `key`, `parameters`, `operations` | override value |
| `harness` | only the fields its overrides set, after the device check |
| `providerDefaults.keySize` | no `keySizes` or `key` override and a key size was observed |
| `providerDefaults.parameters` | no `parameters` override and the provider chose some |
| `providerDefaults.modeAndPadding` | bare name |

## effective.yaml

`schemaVersion: 1`.

| key | holds |
|---|---|
| `generatedFrom` | `global`, `testSet` (the `selection.testSet` string as written), `inventory`, `capture`, `trial`, `device` |
| `run` | the global `run` section |
| `policy` | the global `policy` section |
| `providers.<p>.<type>.<name>` | `keySizes`, `inputSizes`, `key`, `parameters`, `operations`, `providerDefaults`, `harness`; empty ones omitted |
| `providers.<p>.<type>.<name>@<group>` | the same, for one group |
| `warnings` | `exclude_matches_nothing: <rule>`, `override_matches_nothing: <rule>`, then run-level and entry-level `not_supported:` |
| `skipped` | `{stage, provider?, type?, name?, reason}`; preparation writes the same shape with stage `preparation` |

## Errors and writes

| situation | result |
|---|---|
| missing file | `missing_file: <path>` |
| missing test set | `missing_file: <path> (<global> selection.testSet: <value>)` |
| missing facts file | `missing_file: <path> (--facts)` |
| invalid YAML | `unreadable_yaml: <file>: <msg>` |
| `schemaVersion` missing or other | `missing_field` or `unsupported_schema_version` |
| field error | `<file>: <code>: <location>`, e.g. `scope.yaml: unknown_keys: include[0] [nme], known [...]` |
| non-mapping document | `not_a_mapping` |
| YAML loading | SafeConstructor; duplicate keys refused |
| write | `schemaVersion` stamped first, written to `<name>.partial`, moved into place atomically |

## Example

`example/` holds capture, trial, global and test set inputs and the expected inventory and effective outputs. `ExampleFilesTest` compares them; `./gradlew :config:test -Dexamples.update` rewrites the outputs.
