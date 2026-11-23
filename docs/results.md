# Results

- `results/` is gitignored.
- `manifest.yaml` is written last by every run, atomically: a temporary file beside it, then a rename, so a reader finds the old manifest or the whole new one.

## Device folder

```
<results root>/<device_id>/
  discovery/ configuration/ preparation/ benchmark/ analysis/ chart/ check/ interop/ manifest.yaml validation.yaml superseded/ rejected/
  rows.json measurements.json run_log.json primitives.tsv grouping/ summary.json summary.md
  <path_id>/ sites.json app.json ... harness.yaml checked/ report.json report.md
```

perf-repair writes the second and third lines: [artifacts.md](../apps/perf-repair/docs/artifacts.md).

| rule | value |
|---|---|
| `--results` | the root, default `<repo>/results` |
| folder name | `deviceId` of the manifest below, from the probe |
| `--per-suite` | the run's folder is `<root>/<device_id>/<suite>/`, `<suite>` the file stem of `selection.testSet`; laid out as this table's device folder; a session's workers pass it ([sessions.md](sessions.md)) |
| `<root>/.lock` | `--interop`, `--check` and every measuring or probing run hold it from the temporary-folder warning to the manifest (`lib/cryptobench/cryptobench/shared/results/lock.py`, `fcntl.flock`, the holder's pid); a second run on the root stops with `device_busy: <root> is in use by another run (pid <n>); ...` before it writes anything |
| `$XDG_CACHE_HOME/cryptobench/locks/<serial>` (default `~/.cache`) | a `--device` run of the plain, `--probe`, `--check`, `--interop` or `--harness` kind holds it from right after the device connects to the end, the root's `.lock` inside it; the serial is `ANDROID_SERIAL`, else `adb get-serialno`; a second run on the phone stops with `device_busy: phone <serial> is in use by another run (pid <n>); ...` before it writes anything; a blank or `unknown` serial prints `warning: unstable_id: ...` and takes no phone lock; `--identify`, `--devices`, `--session` and `--check-session` take none (a session's workers do) |
| staging | discovery and configure run in `<root>/.staging-*`, then move in; a run that fails there removes it and changes nothing |
| a finished device | a folder whose `manifest.yaml` has no top-level `partial:` (`lib/cryptobench/cryptobench/shared/paths/results.py` `finished`); every reader that lists devices or decides "beside a finished run" asks it |
| unit | `manifest.yaml`, `configuration/`, `preparation/`, `benchmark/`, `analysis/`, `chart/`, `check/`, `interop/`, `validation.yaml`; `discovery/` too under `--discovery overwrite` |
| a publish | the unit already in the folder, finished or not, is renamed whole (but for a resumed run's kept blocks, [below](#resuming-a-stopped-run)) into `superseded/<UTC stamp>[-<n>]/` (manifest first), one line `warning: run_superseded: <folder>: <names> moved to <path>`; then the staged folders move in; nothing is deleted |
| fewer `processRepetitions` or passes on a rerun | the earlier `process-<n>/` and `<pass>/` folders move aside inside `benchmark/` with the unit; `benchmark/` holds only this run's |
| `superseded/<stamp>/` | one earlier unit, the device folder's own layout; `-<n>` from 2 on when that second already has one; nothing reads it |
| `rejected/<stamp>/` | one launch attempt that failed a result rule: `[<pass>/]process-<n>/<id>.json` (when the device wrote one) and `why.yaml`; not part of the unit, so it stays across publishes; never pruned ([validation.md](validation.md#case-rules)) |
| `superseded/` disk use | never pruned; removed by hand; a publishing run's last line, when the folder exists, is `warning: superseded_kept: <folder>/superseded: <n> earlier units, <size> MB; never pruned, remove by hand` |
| a crash during the move-aside | the unit may be split across two `superseded/<stamp>/` folders, or partly still in place for the next publish to move; every file is in one of them |
| `--discovery` | `overwrite`: the old `discovery/` moves aside with its unit; `keep` and `reuse` add to it, and it stays |
| `--interop` | discover, configure and check the pairs inside the stage; beside a finished run: adds `interopPlan`, `interop` to its manifest, its capture to `discovery/`, `interop/` replaced, with the interop's own `configuration/` (`effective.yaml`) under it; the run's `configuration/` and the other keys stay; else a publish whose manifest lists `interopPlan`, `interop` |
| `--check` | the same publish (`lib/cryptobench/cryptobench/shared/results/publish_unit.py`), one `results:` line either way; beside a finished run: adds `check` to its manifest, its capture to `discovery/`, `check/` replaced, with the check's own `configuration/` (`effective.yaml`, `guide.yaml`, `known-answers.yaml`, ...) under it; the run's `configuration/` and the other keys stay; else a publish whose manifest lists `guide`, `knownAnswers`, `check` |
| `--harness` | writes `checked/` beside `harness.yaml`, itself laid out as this table's device folder without the device level |
| a killed process | `.staging-*` stays behind and nothing reads it; a device folder it was measuring has no manifest, reads as unfinished, and the next publish moves it aside |
| root under `/tmp`, `/var/tmp`, `/var/folders` or the system temp folder | one line `warning: results_in_temp: ...`; the run goes on |

## Resuming a stopped run

`lib/cryptobench/cryptobench/stages/measurement/resume.py` decides at the publish of a measuring run (`--bench`, `--device`, not `--probe`); `lib/cryptobench/cryptobench/stages/measurement/session/blocks.py` records and skips blocks.

| rule | value |
|---|---|
| block | `run.resumeBlockRuns` (k, default 10) consecutive runs of one pass: block b holds runs `(b-1)k+1 .. min(bk, processRepetitions)`; passes are blocked each on its own |
| finished block | every run of it closed (each case measured or a coded `case_failed`/`bench_failed` line), the boot id equal at its start and end; then `<pass folder>/blocks/block-<b>.yaml` is written (durable, exclusive) |
| identity | `run`: effective.yaml's `run:` block; `selection`: sha256 of effective.yaml without `run`, `runId`, `generatedFrom`, `analysis` and each entry's `from`; `code`: `timed`, tree digest of `Repo.timed_code` under the repository root (main sources of jca, settings, records, catalogue, files, document, environment/contract, preparation, benchmark; the android module's sources and `build.gradle`; the CLI's main sources; `apps/benchmark/gradle/libs.versions.toml`; `algorithms/setup-catalog.yaml`, `algorithms/engine-operations.yaml`; desktop litter left out), and `runner`, tree digest of `Repo.runner_code` (`lib/cryptobench/cryptobench/stages/measurement/**/*.py`, `apps/benchmark-runner/energy/**/*.py`, `apps/benchmark-runner/energy/*.pbtx`); `device`: the capture's `runtime` block, on a device with `build` from `facts.yaml` beside it (`securityPatch`, `apex` versions of `com.android.conscrypt` and `com.android.art`; [facts.yaml](#factsyaml)); `order`: `{scheme: shuffled, seed}`, `seed` `run.orderSeed` (`variant_order.chosen`); `suppressErrors`: `--suppress-errors` as a sorted set; `schema` 3; `lib/cryptobench/cryptobench/shared/results/identity.py` |
| run record | the identity with `energyAcceptUnresponsive` (`--energy-accept-unresponsive`), `commit` (`git rev-parse HEAD`) and `clean` (`git status --porcelain` empty) of the checkout; git that cannot say stops the run `missing_field: commit, ...`; `RUN_KEYS` and `FLAGS` there classify every effective run key and `pipeline.py` flag as DATA or NOT_DATA (`apps/benchmark-runner/tests/test_run_contract.py`): a DATA run key :config always writes that is absent stops the run `missing_field: run.<key> in effective.yaml`, a run key no row names `unclassified: run.<key> ...`; every block record's `identity` and the manifest's `run:` hold it; `commit` and `clean` are never compared (`lib/cryptobench/cryptobench/shared/results/run_record.py`) |
| record | `schemaVersion: 3`, `pass` (null for the single pass), `block`, `runs {first, last}`, `repetitions`, `size`, `identity`, `runId` (effective.yaml's, of the run that measured it), `bootId {start, end}` (`/proc/sys/kernel/random/boot_id`; null on a host), `outcome` (`finished`, or `boot_changed` with `warning: boot_changed: ...` in `problems`), `processes: [{repetition, folder, problems, relaunched, findings, files {path: sha256}}]` (`problems`: the lines the run added to the manifest's `problems`; `relaunched`: `[{case, attempt, code}]`, each launch again; `findings`: the block end's `check_run` ([validation.md](validation.md#run-rules)); `files` leaves out desktop litter: `.DS_Store`, `Thumbs.db`, `desktop.ini`, `._*`, `paths.litter`) |
| a finished unit | never resumed: a rerun moves it aside whole |
| an unfinished unit, same identity | per pass the leading blocks whose records verify (schema, identity per key, outcome `finished`, runs, every process entry's `problems`, `relaunched`, `files`) and whose runs pass `check_run` against the record's own run block ([validation.md](validation.md#run-rules)) stay in place with their records and `preparation/`; the rest of the unit moves aside; one line per pass `resumed:   [<pass> pass: ]kept blocks 1-<m> (runs 1-<r>), restarting at run <r+1>` (`every run of it measured` when none is left); the manifest's `resumed:` names them; `validation.yaml` gets every kept run's check (`checkedBy: restart`) |
| a kept run failing only by case | the block stays; `redo:      [<pass> pass: ]run <n>: <id> (<code>), ...` before anything runs; at its place in the run order those cases' files move to `rejected/` and they are launched again in the kept run's folder (its `order.txt` kept; `thermal.json`, `clocks.yaml`, `cpu-pins.yaml` keep the other cases' entries), the run converted again, and its block record rewritten with the new `problems`, `relaunched`, `findings`, `files` |
| a record that does not verify | `warning: block_unverified: <record>: <reason>; it and every later block of this pass are measured again`; a reason is also a run's fail without a case (a run file missing, added or changed: `files_differ`) or any fail in a run holding an energy file (`energy.json`, `energy-dry.yaml`, `energy-samples.yaml`), whose capture spans the process |
| an unfinished unit, other identity | `warning: identity_changed: <fields>; starting fresh` (`run.<key>`, `code.<key>`, `device.<key>` with nested keys dotted, e.g. `device.build.securityPatch`, `code.runner`, `selection`, `order`, `suppressErrors`, `schema`), then the whole unit moves aside; a record of an older schema is such a change; a new fingerprint is a new device folder, so nothing is compared |
| kept runs | not launched again; their `benchmark.json` joins `MergeRunsKt`, their files the manifest's lists and their recorded lines `problems`, so the folders are `process-1..N` as in an uninterrupted run |

## Layout

Paths relative to the device folder.

| path | files | when |
|---|---|---|
| `manifest.yaml` | run index | every run |
| `discovery/` | `probe_<stamp>.yaml`, `trial_<stamp>.yaml`, `requirements_<stamp>.yaml` | every run |
| `discovery/` | `facts.yaml`; the whole device plan directory | `--device` |
| `discovery/` | `energy.yaml`, `energy-preflight/{idle.pbtx,busy.pbtx,idle.pftrace,busy.pftrace,idle-end.pftrace}` (rails), `energy-preflight/` power profile (manafa) | energy capture |
| `configuration/` | `inventory.yaml`, `effective.yaml`, `report.yaml` | every run |
| `preparation/` | `prepared.yaml`, `skipped.yaml` | `--bench`, `--device` |
| `benchmark/` | `benchmark.json` | `--bench`, `--device`, at least one case not `dry` |
| `benchmark/process-<n>/` | one run's files; with `run.passes`, the n-th process of every pass merged | `processRepetitions` > 1 |
| `benchmark/<pass>/` | one pass's files, `process-<n>/` under it; `benchmark/benchmark.json` merges them per metric | `run.passes` ([device-session.md](device-session.md#passes)) |
| `benchmark/` | `benchmarkData.json`, `clocks.yaml`, `thermal.json`, `cpu-pins.yaml` when written | `--device` |
| `<pass folder>/blocks/` | `block-<b>.yaml`: one finished block's record ([below](#resuming-a-stopped-run)); the pass folder is `benchmark/` or `benchmark/<pass>/` | `--bench`, `--device` |
| `validation.yaml` | per run the last `check_run` result ([validation.md](validation.md#validationyaml)) | `--bench`, `--device` |
| `<results root>/audit.yaml` | the campaign audit ([validation.md](validation.md#audit)) | `--audit` |
| `benchmark/cases/` | `<id>.json`: one case's pulled `benchmarkData.json`, in each process folder | `--device` ([device-session.md](device-session.md#one-process-per-case)) |
| `benchmark/order.txt` | the case ids in the order the process launched them, in each process folder | `--bench`, `--device` |
| `benchmark/` | `energy.json`, `traces/` (`*.perfetto-trace`, `dry.pftrace`), `energy-dry.yaml`, `energy-samples.yaml` (energy pass); `manafa/` (`manafa.log`, power profile) with `energy.source: manafa` | energy capture |
| `scoped/` | `scoped-plan.yaml` with each scope's interop verdict merged in, `scoped-interop.yaml` (the device's verdicts); a failed run keeps only `scoped-plan.failed.yaml` beside `scoped/` | `--harness`, under `checked/`: [scoped.md](../apps/benchmark/modules/android/docs/scoped.md) |
| `check/` | `check.yaml` (one record per case), `preparation/` (that process's `prepared.yaml`, `skipped.yaml`); `configuration/` (the settings it ran with) when published beside a finished run | `--check`: [check.md](../apps/benchmark/modules/benchmark/docs/check.md) |
| `interop/` | `interop_plan.yaml` (the plan, copied), `interop.yaml`; `configuration/` (the settings it ran with) when published beside a finished run | `--interop`: [interop.md](../apps/benchmark/modules/preparation/docs/interop.md) |
| `analysis/` | `summary.md`, `run-counts.md` (per case: runs, iters per run, calls per iter, runs discarded for heat, seconds waited for temperature), `credibility.md`, `credibility.json`, `qq/<case>.png` ([tools.md](tools.md#credibilitypy)), `throughput.png`, `latency.png`, `stability.png`, `<metric>-vs-time.png` | with `benchmark.json` |
| `chart/<run-id>/` | `summary.md`, `chart-data.json`, `manifest.yaml`, IQR bars per chart group | with `benchmark.json`; `analysis.dir` moves it |

- Energy file fields: [energy.md](energy.md#outputs).

## manifest.yaml

| field | value |
|---|---|
| `schemaVersion` | 1 |
| `mode` | `host` or `device` |
| `config` | path of the `global.yaml` used |
| `deviceId` | from the probe's runtime: `<model>-api<sdk>-<hash>` on Android, `host-<os>-<arch>-jdk<major>-<hash>` on a host; hash = first 8 hex of sha256 over the build fingerprint (host: `java.vendor`, `java.runtime.version`); bundled providers and serials are not in it; a probe without these fields stops with `device_id_fields_missing` |
| `inputs` | `bundled`: sha256 of `providers.bundled`; `config`: sha256 of `global.yaml` without that list, parsed (comments and key order change nothing), with its `selection.testSet` file, `analysis` left out since it only shows results (`lib/cryptobench/cryptobench/shared/results/run_inputs.py`); perf-repair's device stage compares them to decide what reruns |
| `run` | the run record ([Resuming a stopped run](#resuming-a-stopped-run)) of a probing or measuring run; absent from `--check` and `--interop` units |
| `units` | `analysis.units` from `effective.yaml`: `{latency: ms\|us\|ns, throughput: MB/s\|MiB/s\|ops/s}`; every view of the run reads it (charts, summaries, perf-repair's report and renders); absent when `effective.yaml` has none, read as `{latency: ms, throughput: MB/s}` |
| `runtime` | `benchmark.json` runtime if measured, else the probe runtime; `cpuLocked` added when clocks exist |
| `providers` | `name`, `precedence`, `serviceCount`, sorted by precedence |
| `files` | stage outputs, paths relative to the device folder |
| `counts` | `prepared` (`prepared.cases`), `skipped` (`skipped.skipped`), `measured` (`benchmark.cases`) |
| `operations` | per engine type the operations the harness times, from `algorithms/engine-operations.yaml`; a type absent falls back to `TYPE_DEFAULT`, which times nothing |

- `files` keys: `probe`, `trial`, `inventory`, `effective`, `report`, `guide`, `energyCapability`, `energy`, `clocks`, `cpuPins`, `prepared`, `skipped`, `benchmark`, `processes`; `--harness` adds `scopedPlan`, `scopedInterop`; `--interop` adds `interopPlan`, `interop`; `--check` adds `check`, and `knownAnswers` when it publishes its own unit.
- A key is absent when its stage did not run.
- `energy`, `clocks`, `cpuPins` are single paths when `processRepetitions` = 1, lists otherwise.
- `problems`: coded lines of what the run survived, each line once in first order (a block record's `processes[].problems` keeps every process's own), absent when there were none: `energy_failed: <message>`, `idle_start_only: …`, `idle_span_short: …` ([energy.md](energy.md#outputs)); `case_failed: <id>: <reason>` for a case whose own process, or a hook around it (`hook_failed: ...`), failed ([device-session.md](device-session.md#one-process-per-case)); `bench_failed: <message>` when a host `BenchKt` died after writing some rows, which the run keeps; `thermal_gate_timeout: <id>: <pass>: ...` for a case the thermal gate started past its timeout ([device-session.md](device-session.md#thermal-gate)); `not_measured: <id>` for each case of `prepared.yaml` not `dry` that the final `benchmark.json` lacks, whatever lost it (the device run, `ConvertKt`'s `not_in_plan`/`no_metrics`/`not_converted`, `MergeRunsKt`'s `not_merged`, a plan-check refusal in `skipped.yaml`); each is also printed.
- A run whose energy is estimated has a top-level `energy: {source, kind: estimated}`; any other run has no `energy` key.
- A resumed run has a top-level `resumed:` list, one entry per pass that kept blocks: `{pass, blocks: "<first>-<last>", runs: "<first>-<last>", runIds: [...]}`, `runIds` the runs that measured the kept blocks; read at publish, before the run records any block ([Resuming a stopped run](#resuming-a-stopped-run)).
- A measuring run that stopped (an interrupt, a stop signal, an error) has a top-level `partial: {reason, caseRuns, cases, processes}`: `reason` is `interrupted` or `<Type>: <message>`, `processes` maps each folder holding `cases/` (relative to `benchmark/`, `.` for itself) to its case files, `cases` counts distinct ids; `files` lists what the run wrote up to the stop with the pulled `prepared` and `skipped`; a failed write prints `warning: partial_manifest_failed: ...`. A killed run (SIGKILL, host crash) writes no manifest.

## benchmark.json case fields

Beside `metrics` and `parameters` ([measure.md](../apps/benchmark/modules/benchmark/docs/measure.md)), a device case carries:

| field | value |
|---|---|
| `thermalThrottleSleepSeconds` | Jetpack's heat pauses for this case, from `benchmarkData.json`; summed over merged processes |
| `thermal` | `{start: {<sensor>: <C>}, end: {<sensor>: <C>}, startStatus: <n>, endStatus: <n>}` around the case ([device-session.md](device-session.md#temperature)); merged processes keep the first start and the last end; values null when unavailable |
| `thermalNote` | present when a reading is missing (its reason) or cached (`source: cached`) |
| `gate` | `{waitedSeconds: <s>, target: <C>, discards: <n>}`: the host's wait before the case ([device-session.md](device-session.md#thermal-gate)); `waitedSeconds` 0 when it started at once; merged processes add `waitedSeconds` and `discards`, the first `target`; the merged file keeps the timing pass's, each pass's own under `benchmark/<pass>/`; absent when no gate ran |
| `metrics.energyJ.idleBaseline` | rails only, beside `source` and `kind`: `interpolated` or `idle_start_only`, from that process's `energy.json` ([energy.md](energy.md#outputs)); a case merged from processes with different baselines (pass merge and `MergeRunsKt`) keeps its pooled runs, marked `mixed` |

Every timing and allocation row (host and device) carries `gcCleanNs` and `gcCount` in `metrics`, `iterations` 1, one value per sample: the pause of the forced GC and finalization between samples, and the GCs that still landed inside the sample; the device adds `gcBlockingCount`. Neither is part of `timeNs`; `analysis` shows both in `summary.md`. The energy pass collects nothing between samples and has neither.

Every case (host and device) also carries `variant` ([measure.md](../apps/benchmark/modules/benchmark/docs/measure.md#benchmarkjson)): one key after `keyKind`, `"variant": "fixed"` or `"variant": "notFixed"`. A reader (perf-repair's side) groups by the case id without its last part `_<variant>` for the item, and never mixes the two values: `fixed` is the call with the setup the API lets a caller keep, kept (`prepared.yaml` `perCall` names exactly what it still redoes: `operation` or `initAndOperation`), `notFixed` is `getInstance` + init + operation per call. Key generation rows are `fixed` only.

A reader of `gate` (perf-repair's side): `discards` counts the runs of the case thrown away for heat; a wait past `pollTerminateMinutes` ends the benchmark with `temperature_gate_timeout`, so no row records one; `waitedSeconds` is host time outside the timed loop and never part of a metric.

## clocks.yaml

| field | value |
|---|---|
| `schemaVersion` | 1 |
| `locked` | `true`, `false` or `unknown` |
| `before`, `after` | per core: `core`, `index`, `online`, `governor`, `minKhz`, `maxKhz`, `cpuMaxKhz` |
| `cases` | per case `start` and `end`, each `{core: maxKhz}` of the online cores capped below `cpuMaxKhz`; `{}` none |

## facts.yaml

| field | value |
|---|---|
| `schemaVersion` | 1 |
| `os.sdkInt` | device SDK level |
| `rooted` | see [run.md](run.md#device-facts) |
| `cpu.cores` | per core: `core`, `online`, `maxKhz` |
| `pinning` | see [run.md](run.md#device-facts) |
| `build.securityPatch` | `getprop ro.build.version.security_patch`; null with `warning: facts_unknown: build.securityPatch: ...` when empty |
| `build.apex` | `{com.android.conscrypt, com.android.art}`: each module's active `versionCode` in `/apex/apex-info-list.xml` (Android 11 and later), else in `pm list packages --apex-only --show-versioncode` (Android 10, where the list is absent and ART is `com.android.runtime`, so `com.android.art` is null), null for a module the source lacks, both null below SDK 29 (no APEX; nothing is read); read once per run, the probe store's key records the same; the whole map null with `warning: facts_unknown: build.apex: ...` when neither source names an active module |
