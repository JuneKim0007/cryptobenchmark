# Energy from manafa

The `energy.source: manafa` adapter. Shared capture modes and `energy.json`: [energy.md](energy.md).

## Dependency

- Optional: `apps/benchmark-runner/energy/requirements-manafa.txt` into `--energy-python`; imported lazily.
- Missing fails with `manafa_missing: <detail>`.

## Session

| `manafa` fact | value |
|---|---|
| process | `manafa_session.py` holds one `EManafa` per repetition, from before the device run to the end of `joules` |
| profiler | `legacy`: cpufreq and batterystats, also on a device with rails |
| window | case window on BOOTTIME + `boot_time`, passed to `get_consumption_in_between` |
| joules | gross whole-device estimate; `netJoules` is null |
| device effects | `dumpsys batterystats --reset` on start, `killall perfetto` on init and stop |
| `measured` capture | a Jetpack per-case trace stops other Perfetto sessions; windows after the last cpufreq event are `window_uncovered` |

## Pre-flight

`energy.source: manafa` pre-flight: a 3 s session, stopped and read back; `discovery/energy.yaml` records it. The host fails with `manafa_cannot_start: <reason>` when it gives no number.

| manafa `energy.yaml` field | value |
|---|---|
| `schemaVersion`, `source`, `kind` | 1, `manafa`, `estimated` |
| `started`, `usable`, `reason` | the session started; it gave a number; why not |
| `cpuFrequencyEvents`, `batteryStatsEvents`, `joules`, `windowSeconds` | what the session read |
| `powerProfile` | file name of the profile manafa used |

## Not measured

- `joules` and `joulesPerOperation` are null, `notMeasured` holds the reason, `invalid` is `not_measured: <reason>`.

| `not_measured` reason | condition |
|---|---|
| `window_uncovered` | window outside manafa's first and last cpufreq event |
| `no_batterystats` | no batterystats samples; manafa's fallback multiplies by millivolts |
| `no_operations` | no operations in the window |
| `no_estimate: <n>` | total not a positive finite number |
| `consumption_failed: <detail>` | `get_consumption_in_between` raised |
| `manafa_stop_failed: <detail>` | `stop` raised; applies to every case |
