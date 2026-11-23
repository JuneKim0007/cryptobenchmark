# generated

`inventory.yaml` (what the device has), `effective.yaml` (what will run) and `report.yaml` (what the build noticed), written by `Configuration(output)` into `output`. Pipeline output directory: `docs/results.md`. Authored inputs: [config.md](config.md).

## Flow

```
probe_<utc>.yaml + trial_<utc>.yaml -> InventoryBuilder -> inventory.yaml
global.yaml -> selection.testSet -> testsets/<name>.yaml -+
inventory.yaml + facts.yaml (optional) --------------------+-> EffectiveBuilder -> effective.yaml + report.yaml
```

| call | does |
|---|---|
| `inventory(captureFile, trialFile)` | deletes the old inventory; reads capture (schema 1) and trial (schema 3, its `keystore` section required: `missing_field: keystore`); writes inventory |
| `effective(globalFile, inventoryFile, factsFile?)` | deletes the old effective and report; reads global and its test set; writes report, then effective |
| `readEffective()` | reads `effective.yaml` back, with `warnings` and `skipped` of the `report.yaml` beside it when present |

Host entry `ConfigureKt`: `docs/tools.md`.

## inventory.yaml

| rule | value |
|---|---|
| entries | one per trial default run, service and transformation; trial entries without `defaultRun` are left out |
| provider order | capture precedence, then providers seen only in the trial |
| entry fields | `runs`, `keySizes`, `inputSizes`, `keyAlgorithm`, `keyProvider`, `providerChose`, `bareName`, `reason`, `aliases`; empty ones omitted |
| `aliases` | the aliases the capture lists for the service of that provider, type and name (OIDs among them); a transformation has none |
| `inputSizes` | recorded only when the run's input size differs from the trial's `defaultRunInputSize` |
| `reason` | trial error, else `failed` |
| `generatedFrom` | `capture`, `trial` file names; `device` = the capture's `runtime` block |
| duplicate | two names with one canonical name and key size in one provider and type (a provider registering a second spelling as its own service): the first in trial order is kept, the other left out with the warning `duplicate_name: <provider>.<type> <kept> and <left out> are one name; <left out> left out` |
| `keystore` | the trial's keystore rows `{provider, type, algorithm, backing, keySize?, curve?, supported, error?}`; omitted when the trial has none (its section absent on a runtime without a keystore) |
| `warnings` | what the build left out; omitted when empty; `effective` puts them first in `report.yaml` `warnings` |
| refused | an `inventory.yaml` that holds two spellings of one name: `duplicate_name` |
| pairing | capture and trial `capturedAtMillis` differ: `mismatched_trial: capture <a>, trial <b>` |

## Build order

| step | rule |
|---|---|
| select | include (empty = all), then drop anything matching a test-set or global exclude |
| skip | include matching nothing: `no_match: nothing on this device matches the include`; selected with `runs: false`: `not_runnable: <reason>` |
| stop check | under `stop`, any skip fails `stopped_on_failure: <n>` listing the skips |
| resolve | overrides per entry, by precedence in [config.md](config.md#override-precedence) |
| device check | run and entry harness against facts |
| keystore check | an entry whose variants are `[secure]` against the inventory's `keystore` rows of its provider, type, name and backing (`key.backing`, else `tee`): each `keySizes` value whose row is refused is dropped and skipped with the row's `error` (`keystore_unsupported`, `strongbox_unavailable`, `api_too_low`, `not_supported`); without `keySizes`, the row with no size and the curve of a `java.security.spec.ECGenParameterSpec` key spec (none without one) decides the whole entry; every size refused skips the entry; a size or curve the trial has no row for keeps the entry as it is |
| stop check | repeated after the device check |
| empty | nothing selected: `nothing_selected` |

Skips have stage `config`.

## Device support

Facts come from `facts.yaml` (`--facts=`); without it every key that needs a fact is `facts_unknown`. Key rules: `apps/benchmark/modules/settings/docs/settings.md`.

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
| `key`, `parameters`, `operations` | override value; a written key `algorithm` or `provider` checked on the inventory ([entry.md](entry.md#key-source)) |
| `variants` | override, else include, `secure` removed but on a generator; `[secure]` for a generator the trial cannot call; absent when neither asks, so `run.variants` applies ([entry.md](entry.md#variants)) |
| `harness` | only the fields its overrides set, after the device check |
| `providerDefaults.keySize` | no `keySizes` override, no `key` spec tree (a bare `algorithm` or `provider` is none) and a key size was observed |
| `providerDefaults.parameters` | no `parameters` override and the provider chose some |
| `providerDefaults.modeAndPadding` | bare name |

## effective.yaml

`schemaVersion: 2`.

| key | holds |
|---|---|
| `generatedFrom` | `global`, `testSet` (the `selection.testSet` string as written), `inventory`, `capture`, `trial`, `device`; `layers`: `[{path, sha256}]` of each authored layer, lowest first; `settings`: each written `run`, `policy`, `analysis` value and each authored `selection` and `providers` value, by dotted path, to `layer N <file>` or `default`; required, a file without them is refused |
| `runId` | the capture's stamp, `probe_<stamp>.yaml` -> `<stamp>` (e.g. `20261005T103349Z`); absent for a capture named otherwise |
| `run` | the global `run` section |
| `policy` | the global `policy` section |
| `analysis` | the global `analysis` section, defaults filled in |
| `bundledProviders` | the global `providers.bundled` list as written; absent when empty; a repeated artifact or alias is refused with `duplicate_artifact` / `duplicate_alias`. `DevicePlan` installs it before preparing |
| `providers.<p>.<type>.<name>` | `keySizes`, `inputSizes`, `key`, `parameters`, `operations`, `variants`, `providerDefaults`, `harness`; empty ones omitted; then `from` |
| `from` | `testSet` (the `generatedFrom.testSet` file) and `includes`: every include that selected the entry, each `{index, provider?, type?, name?, group?}` with its 0-based position in the test set's `include` list; selection is a union, so no include wins; absent when the test set has no `include` |
| `providers.<p>.<type>.<name>@<group>` | the same, for one group |

## report.yaml

`schemaVersion: 2`. Written beside `effective.yaml`; `effective.yaml` itself carries no `warnings` or `skipped`.

| key | holds |
|---|---|
| `runId` | as in `effective.yaml` |
| `warnings` | the inventory's `warnings`, `variants_fallback:` of global.yaml then of the test set, `exclude_matches_nothing: <rule>`, `override_matches_nothing: <rule>`, run-level and entry-level `not_supported:`, then one `path_not_applicable:` per type and dropped path one `secure_path_unavailable:` (entries asking `secure` of a type whose row lacks it), then with `run.passes` one `shadowed_setting: <path> is unused while run.passes sets the samples of a --device run` per `run.harness.iterations` or `overrides[<i>].set.harness.iterations`, then one `shadowed_setting: <path> is unused by a measured capture; the cool-down applies to dry only` per `run.harness.energy.cooldownSeconds` or `overrides[<i>].set.harness.energy.cooldownSeconds` whose capture is `measured` (the run's only when no override sets `dry`) |
| `skipped` | `{stage, provider?, type?, name?, code, reason?}`; preparation writes the same record ([prepared.md](../../preparation/docs/prepared.md#skippedyaml)) |

## Errors and writes

| situation | result |
|---|---|
| missing file | `missing_file: <path>` |
| missing test set | `missing_file: <path> (<global> selection.testSet: <value>)` |
| invalid YAML | `unreadable_yaml: <file>: <msg>` |
| `schemaVersion` missing or other | `missing_field` or `unsupported_schema_version` |
| field error | `<code>: <file>: <location>`, e.g. `unknown_keys: default_predefined.yaml: include[0] [nme], known [...]` |
| non-mapping document | `not_a_mapping` |
| YAML loading | SafeConstructor; duplicate keys refused |
| write | `schemaVersion` stamped first, written to a unique `.<name>.<n>.partial` beside it, moved into place atomically (`:document` `AtomicFile`) |

## Example

`example/` holds capture, trial, global and test set inputs and the expected inventory, effective and report outputs. `ExampleFilesTest` compares them; `apps/benchmark/gradlew -p apps/benchmark :config:test -Dexamples.update` rewrites the outputs and `tests/contracts/documents/config_global_example.json` and `config_effective_example.json`. The global and test-set examples are the user guide: `ExampleCoverageTest` fails when a key either reader accepts is missing from them or has no comment on its line.
