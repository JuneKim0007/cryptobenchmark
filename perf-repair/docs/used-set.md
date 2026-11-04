# Used set

With `device.filterByApps` (default `true`) the guide hands probe_device the targets' detect, and the device stage runs in two passes, so the apps are scanned on today's probe before anything is measured:

```mermaid
flowchart LR
    P[pipeline.py --probe] --> S[screen: items, signatures, code-made groups] --> D[app step per target, static]
    D --> K[bundled: missing, suggestions, warn or stop] --> Q[probe and screen again when the probe lacks what is applied] --> U[used.json] --> X[used-global.yaml: base + selection.exclude, used-testset.yaml: + include] --> B[pipeline.py --bench / --device]
    B --> I[inbound] --> S2[screen] --> U2[used.json again] --> T[primitives] --> V1[gate: used] --> G[guide grouping: pending in used.json only] --> V2[gate: grouped]
```

| step | rule |
|---|---|
| probe | `pipeline.py --probe` (`--device --probe` on a phone) when the plan reruns the probe; the benchmark run later reuses it on a host (`--discovery reuse`), a phone probes again |
| detect | each target's app step (`perfrepair.app`), no model; an app that fails here stops later at its own app step; the app step does not run twice |
| used | `used.json` ([artifacts.md](artifacts.md#usedjson)): what the sites resolve to, their groups' members, and for an item not yet grouped its candidates, so the benchmark already holds every option the model may later group it with; the model is asked after the benchmark |
| measured set | the used set joined with what device.yaml `benchmark.items` says was measured: a set grows, never shrinks, so a target removed keeps its rows |
| benchmark | reruns for the plan's reasons; a set that grew or shrank reruns nothing: what it lacks is the [gate](#benchmark-gate)'s delta; a record without `benchmark` whose manifest is the base config's measured the whole base selection |
| selection | `used-global.yaml`: the base `global.yaml`, its test set resolved, with one `selection.exclude` rule `{provider, type, name}` per device item (a declared transformation is one) outside the measured set; an item sharing its provider, type and canonical name with a kept one is never excluded; the base test set's includes, groups and overrides stay; `used-testset.yaml` is that test set with one `{provider, type, name}` include per used item the trial can run, in the provider's declared spelling, so a used item the test set lacks is planned (an empty include plans everything and is kept) |
| probe digest | the manifest then carries the generated config's digest; device.yaml `benchmark.config` maps it back to the base digest, so the probe is judged by the base `global.yaml` |
| no item | no target reaches a device item: the base selection is measured, logged `device selection`, device.yaml records no `benchmark` |
| off | `false`: `used.json` removed, every askable item asked; a record with `benchmark` reruns the benchmark on the base config (`device.filterByApps off: ...`) |

- A changed set reruns nothing: a whole rerun is hours and discards valid data; the gate measures only the gap, under the stored setup, with anchors against cross-session drift.
- A first run makes two pipeline runs (probe, then benchmark); later runs with the same targets make none.
- Logged: `device used` (`deviceItems`, `apps`, `sites`, `matched`, `used`, per `via`), `device selection` (`deviceItems`, `measured`, `excluded`), `device grouping` (`items` asked of, `asked`, `notUsed`).
- Each excluded item the base selection never held is one `exclude_matches_nothing` warning in `effective.yaml`: harmless, and the price of not repeating cryptobenchmark's include matching here.

## Benchmark gate

`device/gate.py`, twice per guide run before a model call: after the used set (before grouping assign) and after grouping (the set made again from today's groups, before replace). Unit: (item, operation, variant, key size, input size, metric), each planned case of `prepared.yaml` per metric the perfMode selects; written to `log/details/benchmark_coverage.yaml`, its rows on `primitives_missing.yaml` as `not_benchmarked`.

| class | found | action |
|---|---|---|
| `never_planned` | a used item no case plans (outside the test set) | the delta |
| `lost` | a planned case absent from the rows (`no_samples`, a failed process) | the delta, once |
| `repeats` | lost again after the delta | coded; not sent to the model |
| `refused` | the run log has it `skipped` or `not_runnable` (provider refusal, `not_repeatable`, the keystore provisioning gap) | coded |
| `partial` | the case has rows, not this metric | the delta |
| `low_quality` | fewer runs than `MIN_RUNS` (`result/estimate.py`, the floor pImprove needs) | the delta |
| `no_operation` | the type falls back to `TYPE_DEFAULT` in the harness's `engine-operations.yaml` (`catalog/harness_operations.py`) | coded |

| step | rule |
|---|---|
| onGap | `device.benchmark.onGap`: `delta` (default) measures the delta gaps once per gate point; `stop` ends `not_benchmarked` listing them; a gap left after the delta stops `not_benchmarked`, a fixed stop: a warning would measure, or go on, against what `onGap` or `--device-results` said |
| `--device-results` | no config to run with: `not_benchmarked` with the command that makes the device stage itself |
| device | `--identify` before the delta: another device id than the folder's is `device_id_changed` |
| delta config | `delta/global.yaml`: the stored benchmark's own config (`manifest.config`), run block untouched, its test set's include replaced by the gap items and their anchors, overrides kept |
| printed | `delta:     <n> cases of <k> gap items and <a> anchors, about <m> min at <s> s a case`, from the stored plan and the last `took:      prepare and measure` line |
| session | the same `pipeline.py` run: warm-up, thermal gate (to the stored `thermal.json` baseline through `CRYPTOBENCH_THERMAL_BASELINE`), per-case process, repetitions, variant order, passes |
| anchors | the used items of a gap's family sharing an app with it, measured: every case measured in both sessions is compared on `timeNs` by `change_of` (`result/gain.py`, `criteria.yaml`); one beyond noise and past `improvingRatio` is `setup_drift`, and the delta's cases carry `sessionDrift`; no case compared (no anchor, or overrides left none shared) is `unchecked`: no comparison, so not read as undrifted, a line says why and its estimates carry `cross_session`. `deltas[].comparison` holds `checked`, `setup_drift` or `unchecked`; the delta's line says drift is unreliable on a host, whose clocks are not locked |
| fingerprint | `device/setup_fingerprint.py`, read from the stored benchmark's own files against the delta's, first after a `--probe` so a difference costs no session, again after measuring: device id, build fingerprint, compile mode, SDK or JVM, bundled providers with versions, process files, the energy mark, the effective `run` block and `prepared.yaml` `run`, and per shared case its parameters, harness, metrics and perCall; a difference stops `setup_mismatch` naming the field, nothing merged; `device.benchmark.onSetupMismatch: rerun` measures the whole benchmark again instead, the only whole rerun the gate starts |
| merge | add-only: a case id the stored benchmark holds is refused (`merge_refused`), unequal process files too; new files under `benchmark/merged-<session>/`, `manifest.yaml` renamed in last with `deltas`, so an interrupt leaves the stored benchmark whole |
| after | inbound and primitives again, device.yaml rewritten; `finished.json` sees new rows, the app's static steps rerun, replace asks only scopes whose dossier changed |
| dossier | a pair across sessions is `cross_session` in `needsReview`; across a drifted one its estimate is `setup_drift`, not sent |

- Not recorded, so not compared: the harness APK digest and a Mainline provider update without a build fingerprint change.
- `run.onExisting: overwrite` discards the benchmark (owner decision): no gate rule guards it.

## Bundled providers

A target can ship a JCA provider the device does not register. Measuring without it compares nothing the app runs, so the step after detect names each one, code only, no model (`device/bundled.py`).

| step | rule |
|---|---|
| missing | a provider a target's `app.json` `bundled` names, or a target's site resolved `not_on_device` to, neither among the probe's own providers (`origin` not `bundled`) nor shipped by a group:name in the base `providers.bundled` |
| version | per app its build files' pin (a literal coordinate, a Gradle map, a version catalog entry; several in one app: the newest); apps that differ: the newest not in the row's `badVersions`, each app's pin kept in `missing[].coordinates[].pins`; a variable or a range is no pin |
| `onMissing` (`stops.bundled_missing` when set) | `warn`: one terminate event and line `device bundled_missing: warn`, the run goes on; `stop`: the same event with outcome `stop`, the guide stops `bundled_missing`, listing provider, coordinates and apps, before the benchmark; the probe has run, since detect resolves against it. A stopped run resumes: a kept probe is reused |
| `fromApps` | `off`: no file, the catalog's verdicts are not logged; `suggest`: `bundled-suggestions.yaml`; `apply`: the same, and its matched rows are built in; on a host nothing is built: `applied` stays 0, the `device bundled` line ends `nothing applied: only a --device run builds and installs bundled providers`, and the provider stays missing |
| matched | a catalog row of the coordinate's group:name for that provider, unblocked, at a pinned version not in its `badVersions`; every pin bad: blocked |
| blocked | the row's `blocked` reason; listed, never applied; the provider stays missing |
| unmatched | `no_catalog_row`, `no_coordinates` (a site names it, no build file ships it), `no_pinned_version`, `name_taken` (two rows register one name: the first wins); stays missing |
| apply | `bundled-global.yaml`: the base and the entries, the base's first; the measured set's config is made from it; the per-app harness builds them too, or a candidate from an applied provider would not exist there |
| second probe | when the probe's bundled artifacts are not the config's (`the probe does not hold the providers.bundled this run measures`), probe and screen run again on that config before the used set, so `grouping/items.json` holds the provider's items and the code-made groups cross providers; one more pipeline run, never a model call; a `--device` run only, since a host probe never holds them |
| used set | a harness-bundled provider's item enters `used.json`, so stays measured, only when a site resolves to its type, canonical name and key size; a group or candidate reach alone does not bring it |
| rerun | device.yaml `bundled.applied` holds the entries' digest; a different set reruns the benchmark on today's probe (`the providers.bundled entries device.bundled.fromApps applies changed`). `bundled.bundled` and `bundled.config` map the manifest's digests back to the base's, as `benchmark.config` does, so the base `global.yaml` still judges the probe and an unchanged set runs nothing |

- On a host the base's `providers.bundled` covers no provider: nothing builds it, so it stays missing, `host_cannot_build` in `log/details/primitives_missing.yaml` ([run-log.md](run-log.md)).
- With `device.filterByApps` only: without it nothing is detected before the benchmark, so the step does not run, and any applied set is dropped with a benchmark on the base. `--device-results` names a finished folder, so it does not run there either.
- Logged: `device bundled` (`missing`, `matched`, `blocked`, `unmatched`, `applied`), one `device bundled.<kind>` per non-empty kind with `data.items` (only `missing` with `off`), `device bundled_missing` with `data {code, items}`.
- An applied provider measures under its alias: a site naming the provider's own name still resolves `not_on_device`, and its items enter the used set only through a group whose algorithm another site names.

## Evidence

API 30 emulator capture, grouping rebuilt at profiles schema 4, the apps' `sites.json` resolved on that device, grouping from empty:

| targets | used set (site, group, candidate) | runnable | asked of 46 askable | notUsed | cases of the 100 the base run measured |
|---|---|---|---|---|---|
| none: filter off | 275 | 155 | 46 | 0 | 100 |
| threema | 18 (5, 13, 0) | 14 | 0 | 46 | 36 |
| threema, deltachat, DankChat | 41 (11, 24, 6) | 30 | 8 | 38 | 70 |
| 42 apps with JCA sites (43 folders) | 62 (18, 32, 12) | 44 | 16 | 30 | 72 |

- Dry-run grouping in that order on one folder: 0, then 8, then 16 model calls in total; each new set asked only what it added; the 43-folder set was then 56 items, since an item with a record brings its group, not its candidates.
- The base run there was `testsets/quick.yaml` (20 items); against a full-device test set the measured items fall from 155 runnable to 14, 30 and 44.
- Host check (`config/global-demo.yaml`, the demo app): used set 6 of 214 items, 208 exclude rules, the 3 smoke cases measured; the second run reused every stage and made no pipeline run.
