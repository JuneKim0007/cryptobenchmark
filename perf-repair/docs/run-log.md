# Run log

## Diagram

```mermaid
flowchart LR
    S[stages: log/emit.py emit, step] -- event records --> K[log/sink.py EventSink]
    P[benchmark_runner, device/energy.py, app detect] -- finding events --> K
    K -- one line per event --> E[log/events.jsonl]
    K -- views.py, per event --> V[status.log, ai/stage.log, bug.log]
    E -- views.py render --> V
    E --> W[watch, log summary]
    R[benchmark_runner] -- transcript --> T[log/pipeline/run id.log]
    M[model roles] --> J[role dir journal.jsonl, errors.jsonl]
```

## Files

Every command appends to `<device>/log/`; nothing in it is read back by a stage.

| file | holds |
|---|---|
| `events.jsonl` | one JSON line per event, every field on every line (`dto/event.py`, schema 1); the only stream commands write |
| `status.log` | one line per outcome a person acts on, a `run` header and `end` line per run |
| `ai/screening.log`, `ai/classify.log`, `ai/grouping.log`, `ai/supervisor.log`, `ai/worthiness.log`, `ai/replace.log` | one model stage's events, one line each, problems indented; `classify` is screening's classify role, `supervisor` grouping's review role |
| `bug.log` | each exception that is not a coded error, with its traceback |
| `pipeline/<run id>.log` | the cryptobenchmark transcript of every `pipeline.py` call of one run, each headed `# <stage>[ app <app>]` and `$ <command>` |

- `status.log`, `ai/*.log` and `bug.log` are views: each line is a function of one event (`log/views.py`); `render()` recomputes them from `events.jsonl`.
- `pipeline/<run id>.log` and the role journals are no views; an event's `ref` points into them.
- `log/screening/ai.log` and `log/grouping/ai.log` are no longer written: their lines are in `ai/classify.log`, `ai/grouping.log` and `ai/supervisor.log`; a folder written before keeps the old files, and `render()` over its `events.jsonl` gives the new ones.
- `<results root>/pipeline.log` is no longer written; the transcript is in the device folder, one file per run.

## Status lines

Each line starts with a code word, then what it is about, then `: <detail>`; `log/status.py` renders one function per line kind.

| event | line |
|---|---|
| `run_start`, `run_end` | `run <run id> <ts>: <command>`; `end <run id>: <exit> (<s>)` |
| `finding` from `terminate` ([stops.md](stops.md)) | `<code> <subject>: [<action>: ]<detail>[; see <ref>]; next: <next step>`; the subject is the item (and `app <app>`), else `app <app> at <step>` or `guide <step>` for the guide, else `<stage> <step>`; the action is shown when it is `warn` or `skip` |
| guide `target` end | `ok`, `reused` or `not_run app <app>[: <detail>]`; a stopped app has its `terminate` or `bug` line only |
| device stage end | `ran` or `reused device <stage>: <reason>`; `failed device <stage>: <error>` for a failure no `terminate` reported |
| `error`, `bug` | `<code> error: <detail>`; `bug <stage> <step>: <type>: <message>; traceback in log/bug.log` |

| code | emitted by | item, detail |
|---|---|---|
| `not_on_device` | `perfrepair.app`, after its files are written | the provider; its sites |
| `energy_invalid` | `device/energy.py`, after each device run | the case id; its reasons across process files (`short_window`, `window_uncovered`, ...); ref: the `energy.json` |
| `energy_unreadable` | `device/energy.py` | the manifest; the run stands |
| `pipeline_failed` | `benchmark_runner.py` | the stage; exit and last error line; ref: `pipeline/<run id>.log:<line>` of the call; the device step, the guide step and the app's target add no line |
| `perf_mode_unmeasured`, `perf_mode_maybe_unmeasured` | `device/measures.py` | the metrics |
| `bundled_missing` | `device/bundled.py` | each provider with its coordinates and apps |
| a guide stop (`no_options`, `missing_device_stage`, `<step>_failed`, ...) | `guide/steps.py`, `guide/run.py` | `<step>_failed` carries the inner code in `data.inner` and first in its detail |

- The code is `data.code`; an event written before it has its detail's first word holding an underscore, or one word before a colon.
- A step that ends in a `Halt` records `data.code` and `data.reported`; its own line is left out.
- A line adds the last `error` line of its detail.

## Event fields

| field | holds |
|---|---|
| `ts`, `run` | UTC time to the millisecond; the id of the command's run, shared by commands it calls in-process |
| `stage`, `step`, `item`, `app` | where: `device`, `inbound`, `grouping`, `screening`, `app`, `repair`, `replace`, `worthiness`, `report`, `guide`, `run`, or a logger's package for a log record |
| `kind`, `event` | `static` or `model`; `start`, `end`, `turn`, `decision`, `run_start`, `run_end`, `error`, `bug`, `finding`, `log` |
| `outcome`, `durationMs`, `detail` | `ok`, `ran`, `reused`, `failed`, `accepted`, `rejected`, `refused`, `decided`, `dropped`, a finding's code, a log level, a run's exit; time; a reason or message |
| `tokens`, `costUsd` | a turn's usage from the reply: `input`, `output`, `cacheRead`, `cacheWrite`; the CLI's `total_cost_usd`, null from the API and dry-run gateways |
| `ref` | `<role dir>/journal.jsonl:<line>` for a turn, the outbox record for a decision, the file a finding names, relative to the device folder |
| `data` | `counts` and `files` (path → sha256) of a step's end; `session`, `turn`, `problems`, `outbox` of a model event; a start's `pending` and outbox `opened`, `resumed` or `rotated` |

## Rules

- A static step emits `start` and `end`; a model step emits `start`, a `turn` per model call, a `decision` per committed item, `end`.
- No prompt or reply text is in an event; the journal line and the outbox record hold it.
- Records logged before the device folder is known are kept and written, in order, once it is; a command that never names an existing folder writes nothing.
- Each line is one append of a whole line; a reader takes only lines ending in a newline, and the validator reports a partial last line.
- The stderr lines are the same as without the log: event records stay off stderr, and setting lines at DEBUG reach only `events.jsonl`.
- A `Halt` is its `terminate` finding and `error <code>: ...` on stderr; another coded error is one `error` event with `data.code` and the same stderr line, none when its command runs inside another; any other exception is a `bug` event, `error bug: <type>: <message>; traceback in <device>/log/bug.log`, exit 1; before the folder is known the traceback goes to stderr.
- `watch` prints one line per finished step, a finding's status line, and a counter per model step, `grouping assign 37/176 · 2 rejected · $0.0040 · 41s`, rewritten in place on a terminal with each turn, one line per decision elsewhere; it exits 0 when the last line it read is a `run_end`, 130 on Ctrl-C; without `--from-start` it starts at the file's end; with it, every run in the file replays, each `run_start` resetting the counters.
- `log summary` takes every run of the folder unless `--run` names one or `--last` asks for the newest: a line per run (a run with no end is `running` if newest, else `unfinished`), the total, then per stage and per app folder its time (the sum of its step ends, plus the turns of a model step a killed run left open; an app folder leaves out the guide's steps), each static step's runs and time, items and decisions, model calls, rejections and their top problems, the slowest items, tokens and cost; last `status:`, the status lines of the runs shown (`status` in `--json`).
