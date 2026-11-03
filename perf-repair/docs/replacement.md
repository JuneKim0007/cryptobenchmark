# Replacement

From an app's source to a measured before/after of each call site the model chose to replace. Types: `src/perfrepair/dto/site.py`.

## Flow

| step | who | reads | writes |
|---|---|---|---|
| detect | static | app root; engine types from the packaged names catalog; the run's probe and providers to resolve each site | `<app>/sites.json` |
| scope | static | sites, app source, `scope/engines.yaml` | `<app>/scopes.json` (schema 4; `Scope` per site: function span, sinks, key source, `lifecycle`) |
| units | static | scopes, app source, `scope/units/relations.yaml` | `<app>/units.json` (`Unit`: members, `Link`s with lines on both sides, the units it shares a function with) |
| dossier | static | scopes, units, app.json `targetSdk`, `grouping/groups.json` (with its `interop` section), `grouping/screen.json`, `measurements.json` | `<app>/dossiers.json` (schema 2; `Dossier`: function source, current item, `Option`s with interop status and `Estimate`s; `units`: the units asked) |
| replace | model | one unit, every member's `Dossier`, per conversation | `<app>/replace/` outbox, `replacements.json` (`Replacement`) |
| edit | static | replacements, app source | `<app>/patched/` (a copy; the app is never edited), `edits.json` |
| harness | static | scopes, dossiers, the original and patched function, the results' `effective.yaml` | `<app>/harness.yaml` for cryptobenchmark; inputs with their source (`docs/repair.md`) |
| measure | device | `harness.yaml` | `<app>/measured/scoped/`: `scoped-plan.yaml` (compile and interop per scope), `benchmark.json` (cases `scope:<id>:before`, `:after`: `timeNs`, `allocationCount`, `energyJ`) |
| report | static | every file above | `<app>/report.json`, `report.md`; `summary.json`, `summary.md` across apps |

## Guide

```
python3 -m perfrepair guide --app <root> --device-results <device> \
    [--mode latency|battery] [--agent ...] [--auth ...] [--prompts DIR] [--limit N] [--refresh] [--device [--config <global.yaml>]]
python3 -m perfrepair guide --device-results <device> ...   # without --app: every apps.targets entry
python3 scripts/llm_guide.py <same arguments>      # from the cryptobenchmark root; sets the path itself
```

- `python3 -m perfrepair` needs `pip install -e perf-repair` or `PYTHONPATH=perf-repair/src`.
- `--mode`, `--limit` and `--device` default to `apps.mode`, `apps.limit` and `apps.measure`, `--config` to `device.benchmark.config`, the model to the `apps.agent` role; `ai replace` uses the `apps.replace` role (`docs/settings.md`).
- `--refresh` asks again the replace decisions whose dossier changed, and, when the guide runs the device stage (no named folder), rebuilds `primitives.tsv`; without it such an app stops with `dossier_changed` (`docs/decisions.md` Site replace).
- `--device-results` is required unless `paths.results` is set (`docs/settings.md`); keep results under `~/capstone/runs/<date>-<name>`.
- Named folder (`--device-results`, or `device.id`): it must already hold `manifest.yaml`, `rows.json`, `measurements.json` (inbound) and `grouping/groups.json` (grouping build, assign, report): device-level stages, made once per device, never per app; a missing one stops with `missing_device_stage`.
- `paths.results` alone: prerequisites calls probe_device() on that root (`docs/pipeline.md` Device stage; on the phone with `--device`), printing `device <stage>: reused` or `ran: <reason>`; the grouping step asks what coverage finds missing (`docs/pipeline.md` Grouping knowledge) by `grouping assign` and `grouping report`, with the guide's `--agent` and `--perfrepair-config`, and prints `reused`, or what it ran.
- Steps in order: prerequisites, grouping, app (detect and scope), dossier, replace, edit, harness; with `--device`: device (`pipeline.py --device --harness <harness.yaml>`, an attached phone; it writes `measured/` beside the harness), then report. Without `--device` the guide ends at the harness and prints the device command.
- Each step prints `guide <step>: ok: <detail>`; the first failing step prints `guide <step>: stop <code>: <detail>`, and ends that app; a stop in prerequisites or grouping ends the run, exit 1, no app runs.
- Over the apps: prerequisites and grouping once, each app's steps, then `guide summary:` (`report summary` over every `<app>/report.json`; a dry run has none) and one line per app: `app <id>: ok`, `reused`, `stop <code> at <step>: <detail>`, or `not_run <why>`.
- One app's stop, gate rejection or bug (`stop bug at app`, the traceback in `log/bug.log`) is recorded and the next app runs. A provider failure (`claude_cli_failed`, `claude_api_failed`) stops the loop, the rest `not_run`, since every app would fail the same way.
- Exit 0 only if every app reached its last step, the harness or with `--device` the report, or was reused: `no_options` and `no_replacement` count against it, so a run of many real apps usually exits 1 and the per-app lines are the result.
- Reuse is of `apps.targets` only: an app that reached its last step writes `<app>/finished.json`, the digests of its source and build files, its `scopes.json` and `units.json` as the run left them, the scoper version (a digest of the code from app tree to measured harness: perf-repair `app/`, `scope/`, `source/`, `result/`, `repair/`; `scripts/scope_*.py`; the android `Scope*.kt`), `groups.json`, `rows.json`, `measurements.json`, the screening catalog and the replace charter, its mode and whether it was measured; the same on a later run means no step for it, `reused`. `--app`, `--limit` and an app that stopped run every time; a stopped one repays nothing, its replace outbox resumes.

| stop code | step | when |
|---|---|---|
| `target_missing` | the target | an `apps.targets` entry is no folder; its earlier results stay |
| `missing_results` | prerequisites | no `manifest.yaml` in the device folder |
| `missing_device_stage` | prerequisites, grouping | `rows.json` or `measurements.json` absent, `grouping/items.json` absent, or items with no decision in a named folder; the line names the commands |
| `app_failed` | app | `perfrepair.app` exits non-zero, or its gate refuses the folder, whose reason the line carries |
| `several_project_roots` | app | `--app` holds several project roots; pass one of them |
| `no_options` | dossier | no scope has an option; the line lists the `noOptions` reasons |
| `no_replacement` | replace | every scope is kept |
| `dossier_changed` | replace | a decision was made on an earlier dossier; the line names the scopes; `guide --refresh` asks them again |
| `edit_invalid`, `no_edit_applied` | edit | edits.json fails its validator; every edit is rejected, with the reasons |
| `harness_invalid` | harness | harness.yaml fails its validator |
| `<step>_failed` | any | a validation failure, coded `ValueError`, missing file or failed pipeline run inside the step |

## Report

`python3 -m perfrepair.report app --device-results <device> --app <src> [--mode latency|battery]`, then `python3 -m perfrepair.report summary --device-results <device>`. A step whose file is absent is `not_run`; `sites.json` and `scopes.json` are required.

| report.json row field | value |
|---|---|
| `inputs` | the scope's harness.yaml `inputs`: `inputSize`, `keySize`, `from` (`app` or `run`); null when the scope is not in the harness |
| `decision` | `replace`, `keep` or `not_run`; its reason; source `llm`, `fallback` or `static`; `stale` true when replacements.json lists the scope as decided on an earlier dossier, marked in report.md |
| `edit` | `applied`, `rejected` (edits.json reason), `skipped` (not a replace), `not_run` |
| `compile` | `compiled`; `primitive_only` with the scoped-plan reason (`not_compilable`); `not_measurable` with its reason (`no_operation`: a factory, never generated); `skipped`; `not_run` (no device run) |
| `interop` | `passed`, `unchecked`, `not_comparable` (an identity-only output, not measured), `interop_failed`, `call_failed`, with the check and reason; `skipped`, `not_run` |
| `metrics` | `timeNs` (ns/op, with ops/s and MB/s when the case has an input size), `allocationCount`, `energyJ`: median before and after, ratio (after ÷ before; null when before is 0), pImprove and its level, n; `kind: estimated` on an estimated `energyJ`, labelled in report.md and summary.md |
| `verdict` | the mode's rule on the measured ratios: `improves`, `not_improving`, `not_measured` |
| `primitive` | the chosen option's dossier estimates: the benchmark's evidence when the function itself is not measured |

- `energyJ` of different kinds before and after is `{"measured": false, "reason": "energy_kinds_differ: ..."}`.
- A metric without runs on both sides is `{"measured": false, "reason"}`: the first step that stopped, e.g. `primitive_only: missing_input: inputSize for in`. No number is ever filled in.
- `funnel`: sites → scopes → withOptions → replace → applied → compiled → interopPassed → measured; `measured` includes interop `unchecked`, counted again in `measuredUnchecked` (not a stage); report.md marks each such scope "measured without an interop check", e.g. a randomized encrypt with no decrypt partner (`nondeterministic_output`).
- A scoped-plan.yaml whose scopes are not harness.yaml's is `measured_mismatch`.
- summary.json: the funnel summed and per app; per metric each app's ratio is the median over its measured scopes, `improved` at or below `improvingRatio` (`result/criteria.yaml`), `worse` at or above its inverse, else `unchanged` or `notMeasured`; `medianChange` is the median app ratio − 1. Reports of different modes are `mixed_modes`.

## Contracts

- A scope's `lifecycle` (`dto/lifecycle.py`) is evidence beside the function span, never a narrower region: `start`, `end` stay the function's bounds for edit, render and harness. `status` is `bounded` (one method creates, configures and uses the object; no escape, consumer or deferred lambda), `partially_bounded` with its reasons (`field`, `escape`, `wrapper`, `deferred`, `depth1`, `budget`, `configuration_not_found`, `use_not_found`), `no_real_use` (created and never used, nothing escapes), or `unsupported` (`parser_missing`, `engine_unknown`, `call_not_found`). `steps` are the calls on the object, each with role (`configure`, `use`, `consume`, `other`), line and `where` (`same` or `depth1`, one method away in the class); `requirements` name each value a step takes (`key`, `parameters`, `input`) and its origin in a closed list (`parameter`, `field`, `same_class_call`, `other_call`, `generated`, `derived`, `keystore`, `decoded`, `storage`, `literal`, `unknown`) with its line; `operations` are the benchmark operations the steps perform, empty when unknown. The validator refuses a value outside the lists or a cited line outside the file.
- A requirement is open when its origin is in `OPEN_ORIGINS` (`parameter`, `field`, `same_class_call`, `other_call`, `unknown`) and no single closed origin one method away settles it. Code reads on from it in the outermost class of its file: field writes, call arguments in the class, returned values, a branch's operands (never a join's, an array's size or an index), then on from each open one. At most `REACH_METHODS` methods, `REACH_HOPS` hops, `REACH_LINES` values per requirement; past any the requirement stays open, never a wider reading.
- Settlement: when every path closes to one origin, with no path open or cut and no parameter or field other classes can reach, the requirement holds `settled: {origin, line}` and nothing asks.
- Scoping is local and has no cross-file analysis: a requirement from elsewhere (`parameter`, `other_call`, with its line) is a recorded fact, and unknown is an allowed result. A model role choosing among the in-class lines was tried and removed: on a real app it changed no `keySource` and 12 of 25 answers were wrong.
- `origin` on a requirement is what code read and is never rewritten; `status` and `reasons` stay as code read them.
- `keySource` takes a settled key origin only when it is in `KEY_SOURCES` and the view is `unknown` or `parameter`, so a closed reading stays. The `DERIVED_RISKS` rows read `keySource`, so they follow it; `storage` implies `key_compatibility`. Site-replace shows each settled requirement as `settled: <origin>, line <n>`.
- `keySource` is the key requirement's origin when it is one of `KEY_SOURCES` (a field's or a private method's parameter's single origin one method away when there is one), else the pattern match; `sinks` stay the pattern match.
- An `energyJ` estimate carries `kind`; `estimated` also shows in its `configuration`. A pair whose sides differ in kind has no estimate: the option's `noEstimates` lists it with `energy_kinds_differ`. A `benchmark.json` without a kind reads as `measured`.
- An option's estimates cover only the configurations of the lifecycle's `operations` when it knows them; its pins come from every operation, since parameters do not depend on it.

- The app gate finds the outermost Android project roots under `--app`, down to 4 levels: a folder with `settings.gradle(.kts)`, or with `build.gradle(.kts)` beside an Android source set (at `--app` itself, any build file); build, .gradle, .git, .idea and node_modules are skipped and symlinks are not followed. One root is `<path id>`; several become units `<path id>.<root dirs joined by '.'>`. `app.json` `projectRoot` is the root relative to `--app`, and site files are relative to it, so a later `--app`, that project root, reads them.
- A unit is the objects decided, swapped and measured together: the connected components of the links; a scope with none is a unit of one. Only `bounded` and `partially_bounded` scopes link: an object never used or never read has nothing to keep in step. Its `id` is `unit_id(app, members)`. (A multi-root app's `<path id>.<root>` folders are another thing, one per project root.)
- A link names its lines on both sides, and they come from that side's lifecycle. `shared_key`: two key requirements with one origin and one line (a field, a parameter both steps name, one call), never `unknown` or `literal`. `producer_consumer`: an output of a `producers` call (`relations.yaml`) reaching a key requirement: `line`, the requirement's origin is that very line; in one outermost class, `call` (the line calls the producer's function, which returns), `field` (the output is written to the field the requirement reads) or `parameter` (the parameter the step names has the type the producer's method returns, and the names' first segments agree when both are known). `inverse`: one engine type, one algorithm, operations inverse in `relations.yaml`, and `key` or `input` (one origin and one line), `producer` (one producer feeds both) or `parameter` (both take their key from their caller, in one class: the same contract, though no caller is seen; the weakest evidence, kept because it pairs a wrapper's encrypt and decrypt).
- A scope's `id` is `scope_id(app, file, function, line, call)`, so rerunning detection and scoping on the same source gives the same ids, and every later step refers to a scope only by id.
- An `Option` is a member of the site's group that is available in the app's process, from the platform or bundled by the app. Its `pins` are the parameters that make the swap like-for-like (IV length, tag length, OAEP digests); `null` means unknown (no configuration measured on both sides), and the gate refuses a `replace` to it. A benchmark row without `parameters` is the coded error `missing_parameters`.
- An `Option`'s `interop` is `pair_status(groups, current, item)`: `pass`, `not_checkable`, `not_planned` or `not_run`; required, no default. A pair whose interop check failed is never an option; a scope that loses every option that way is in `noOptions` with `interop_failed`. A groups.json without an `interop` section is refused. The validator refuses a status outside that set, `fail`, or one that differs from groups.json.
- An `Option`'s `screen` is the item's status for this app ([screening.md](screening.md) Use): screen.json's verdict, raised to `platform_deprecated` by `ScreeningHandler.for_app` at app.json's `targetSdk`; null without screen.json. A `broken` or `platform_deprecated` item is an option only as the current item's canonical name and key size, at no worse a status than the current's (don't lower the status); a scope that loses every option that way is in `noOptions` with `deprecated_only`. The validator recomputes the app's statuses with the handler and refuses a `screen` that differs or an option that lowers the status.
- A `replace` to an option whose `interop` is not `pass` must declare `unverified_interop` (a `DERIVED_RISKS` row on the option, like the scope rows).
- An `Estimate` is graded, never a gate: `pImprove` is the probability the option is better on that metric. Below 0.95 the report says `warn` with the number; it is `null` when either side has fewer than two runs, rendered `n/a (n<2)`.
- A site whose algorithm name providers disagree on resolves `name_conflict` and reaches `noOptions` as `unresolved`; it never stops the app step.
- `noOptions` reasons are `NO_OPTION_REASONS`, in filter order, the first filter that leaves nothing named: `no_real_use`, `not_on_device`, `unresolved`, `not_grouped`, `no_alternative`, `none_available`, `deprecated_only`, `interop_failed`, `unit_member_without_option` (last: this member has options, another member of its unit has none, so the whole unit is kept). `no_real_use` comes first: the lifecycle shows the object is never used, so no device or app change makes it worth measuring; then `not_on_device`: the site's provider or name is not on the device, so the fix is the device stage (`providers.bundled`), not the app; `deprecated_only` sits after `none_available` (a target that cannot run says so, whatever its status) and before `interop_failed` (a pair never offered needs no interop result). A scope in `noOptions` is never asked: `replacements.json` holds a static `keep` for it whose reason is its code, so it covers every scope.
- The model picks, per unit, one option for every member or `keep` for the unit, and expresses the change only as `Edit`s of a kind in `EDIT_KINDS`. Static code renders and applies them. A replacement whose edits do not apply (`edit: rejected`), do not compile in the harness (`compile: primitive_only`), or fail the interop check (`interop: interop_failed`; data from before the swap must still decrypt after it) is reported with the reason, and is never measured.
- `harness.yaml` names each scope's original and patched function source, its inputs, and its `current` and `option` items. Inputs are the app's static sizes (`from: app`), else the largest sizes the run configured for both items (`from: run`); a parameter type the harness cannot build stays `unsupported_parameter`, never a made-up value. cryptobenchmark compiles both into the benchmark app and measures them like any other case.
