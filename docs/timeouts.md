# Timeouts

Every host subprocess runs under a ceiling from `lib/cryptobench/cryptobench/shared/device/timeouts.py`; past it the process is killed and the run stops with `error: timeout: <step> ran past <s> s: <command>`. A ceiling only catches a hang: each is several times the longest real step, and none is a setting.

| step | ceiling | covers | why this value |
|---|---|---|---|
| `adb` | 10 min | one adb command: shell, push, pull, AOT compile, Perfetto pre-flight | a pull of every case's Perfetto trace is the longest; `cmd package compile` takes under a minute |
| `install` | 60 min | root Gradle `installRelease` and `installReleaseAndroidTest` | a cold build with dependency download takes minutes |
| `case` | 60 min | one case's `am instrument` | one case measures for about a minute |
| `instrument` | 12 h | one `am instrument`: `CryptoBenchmark`'s case listing and warm-up, `DeviceProbe`, `EnergyDryBenchmark`, `InteropCheck` | `EnergyDryBenchmark` and `InteropCheck` hold every case of the test set in one process |
| `gradle` | 4 h | a `tools/` Gradle run: probe, configure, host measure, convert, merge | the host measure of the full test set is the longest |
| `compile` | 30 min | `--harness` scope compile | one compile of the android test sources |
| `energy` | 2 h | `apps/benchmark-runner/energy` (`energy.py`, `preflight.py`), manafa's pre-flight and answer | the trace processor loads one trace per case |
| `analysis` | 30 min | `analyze.py`, `charts.py` | seconds in practice |

- An energy step past its ceiling is `energy_failed: timeout: ...` and the run goes on ([energy.md](energy.md#outputs)).
- Analysis runs `analyze.py`, then `charts.py` ([tools.md](tools.md#chartspy)); a failure is `warning: charts_failed: <reason>`, the benchmark and manifest stay and the run succeeds.
