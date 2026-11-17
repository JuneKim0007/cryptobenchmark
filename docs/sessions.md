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
