# Sessions

## session.yaml

`pipeline.py --check-session SESSION_YAML` reads it; `lib/cryptobench/cryptobench/shared/session/document.py`. Paths are relative to the session file.

```yaml
schemaVersion: 1
name: tiers                  # default: the file's stem
devices:
  emulators: false           # default false: emulators join select: all only when true
  select: all                # all | listed
host:
  benchmark: false           # default false
defaults:
  config: global.yaml        # default: the run's global.yaml chain (run.md)
  suites: [tier1.yaml]       # test-set files; one suite = one run
  order: 0                   # default 0
targets:                     # keys: a device key, an alias, a transport serial, or host
  pixel10: {suites: [tier1.yaml, tier2.yaml]}
  host: {config: host.yaml}
```

| setting | rule |
|---|---|
| `devices.select: all` | every ready device adb lists is a target, with `defaults`; physical only unless `devices.emulators` |
| `devices.select: listed` | only `targets`; a listed emulator runs whatever `devices.emulators` says |
| target key | matched as an exact key, then an alias (`devices.md`), then a transport serial; no prefix or pattern |
| `order` | integer >= 0; one group per value, groups in ascending order |
| host order | `targets.host.order` when set, else one past the highest device order (0 with no device) |
| `config`, `suites` | the target's own, else `defaults` |

## Resolution

`lib/cryptobench/cryptobench/shared/session/targets.py`. A session file that cannot be read stops: `missing_file`, `invalid_yaml`, `unknown_keys`, `not_a_mapping`, `wrong_type`, another `schemaVersion`. Every other problem skips one target:

| problem | line |
|---|---|
| adb lists no such key, alias or serial | `device_not_attached: <target>: ...; attached: <keys>` |
| listed but not ready | the listing's `device_unauthorized`, `device_offline`, `device_no_permissions` or `device_not_booted` line |
| order not an integer >= 0 (a float, text, a boolean, negative) | `invalid_order: <target>: <value>; use an integer >= 0` |
| config or a suite file missing | `missing_file: <path> (<setting>)`; a named file never falls back |
| no suites | `nothing_to_measure: <target>: no suites ...` |
| two suites with one file stem | `target_conflict: <target>: suites ... share the name <stem>` |
| two target keys for one device | `target_conflict: <a> and <b> name one device, <key>`, both skipped |
| `targets.host` with `host.benchmark` false | `host_benchmark_not_set: host.benchmark is false` |

| notice | when |
|---|---|
| `host_benchmark_not_set: host.benchmark is false` | `host.benchmark` false |
| `parallel_unavailable: order <n> has <k> targets; ...` | a group of several targets: they run one after another |

No target left: `nothing_to_measure: no device target is ready or resolved[; host.benchmark is false]`, exit 1.

## --check-session

Prints the device listing, one `order <n>:   <target> (<key>, adb <serial> | host): <suites> -> <results>/<device_id>/<suite>/` line per target in ascending order, the notices as `warning:` lines and each skip as `skipped:   <target>: <line>`. Runs no tool and writes nothing.

## --session

`pipeline.py --session SESSION_YAML [--results DIR] [--stacktrace] [--energy-python PYTHON] [--suppress-errors ERRORS]`; `lib/cryptobench/cryptobench/pipeline/orchestrator/run.py`. Prints the listing and the plan, then runs every target's suites.

| rule | value |
|---|---|
| groups | ascending `order`; a group starts when the previous one ended, failed and skipped targets included |
| within a group | one target after another, its suites in the listed order (`parallel_unavailable`) |
| worker | `pipeline.py --config <suite config> --results <DIR> --per-suite --device` on a device, `--bench` on the host, plus `--stacktrace` and `--energy-python` when given; its own process group; stdin closed |
| `ANDROID_SERIAL` | the target's transport serial on a device worker; an inherited value is ignored with `warning: android_serial_ignored: ...`; `--suppress-errors` (or `CRYPTOBENCH_SUPPRESS_ERRORS`) reaches device workers as that variable; a host worker gets neither it nor `CRYPTOBENCH_SUPPRESS_ERRORS` |
| suite config | the target's config with `selection.testSet` set to the suite's absolute path, written to the session folder |
| a run | one suite on one target, at `<DIR>/<device_id>/<suite>/` ([results.md](results.md#device-folder)); a failed run ends only itself |
| status | one line per target, `target:    <target>: <suite>: <worker's last line>`; redrawn in place on a terminal, else printed when it changes |
| Ctrl-C, SIGTERM, SIGHUP | SIGTERM to the running worker's group, which writes its partial manifest; its group is killed after 120 s or a second Ctrl-C; the summary marks it `stopped` and the rest `not started`; the session then stops as on Ctrl-C |
| end | the summary is printed and written; any row neither `finished` nor `all_skipped` is `session_incomplete: <n> of <m> rows did not finish; see <summary>`, exit 1 |
| `<DIR>/sessions/<name>/.lock` | one session of a name at a time: `device_busy` |

`<DIR>/sessions/<name>/` holds no measurements:

| file | holds |
|---|---|
| `session.log` | one stamped line per event: `session`, `notice:`, `skipped: <target>: <line>`, `start: <target> <suite>: <argv>`, `finished:`, `all_skipped: <target> <suite>: <the manifest's all_cases_skipped line>`, `failed: <target> <suite>: <worker's error line>`, `stopped:`, `summary:`, `index:` |
| `<target>/<suite>.log` | the worker's stdout and stderr, then the session's line for it; `<target>` with characters other than letters, digits, `.`, `_`, `-` as `-` |
| `<target>/target.log` | a skipped target's line |
| `<target>/<suite>.global.yaml` | the suite config |
| `summary.txt` | `target suite state code results`; state `finished`, `all_skipped` (exit 0 and the run's manifest `problems` hold `all_cases_skipped: ...`; code `all_cases_skipped`), `failed`, `skipped`, `stopped` or `not started`; code the first word of the worker's last `error:` line, `subprocess_failed` for an exit without one |
| `index.yaml` | [index.yaml](#indexyaml) |

## index.yaml

`lib/cryptobench/cryptobench/pipeline/orchestrator/index.py`, written after the summary, also after a stop. Read from each run's own files: `configuration/effective.yaml` and `report.yaml`, `preparation/prepared.yaml` and `skipped.yaml`, `benchmark/benchmark.json`.

| key | holds |
|---|---|
| `schemaVersion`, `session` | 1, the session's name |
| `runs[]` | `target`, `suite`, `state`, `code`, `results`: the summary's rows |
| `cases[]` | one per case of every run with `results` |

| case key | holds |
|---|---|
| `id` | the prepared case id; a preparation skip's id from its `<case id>: <code>: ...` reason (an id ends in its variant); null for a config skip |
| `entry` | a config skip only: `<provider>.<type>.<name>` |
| `suite`, `device`, `target` | the suite (the tier), the device folder's name, the session's target |
| `configured`, `prepared` | in effective.yaml; in prepared.yaml |
| `skip` | the skip's code, null when prepared |
| `runs` | the `timeNs` runs benchmark.json holds for the id (the first metric without time), 0 when absent |
| `from` | the prepared case's `from`; for a preparation skip the effective entry's of that provider, type and name; null for a config skip |
