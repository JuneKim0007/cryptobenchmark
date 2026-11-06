# Modes

A decision's mode is its perfMode: which registry metrics (`src/perfrepair/dto/metrics.py`) it is given and judged by. The rule and its threshold are data: `src/perfrepair/result/criteria.yaml`.

## perfMode

| Key | Selects | Shown as |
|---|---|---|
| `latency` | `timeNs` | ms/op by default (`analysis.units.latency`) |
| `throughput` | `timeNs` | MB/s by default (`analysis.units.throughput`); MB/s and MiB/s only where an input size exists |
| `memAlloc` | `allocationCount` | allocations/op |
| `energy` | `energyJ` | J/op, with its kind |
| `generic`, `all` | every key above: `ALL_KEYS` beside the registry, a metric added there included | every unit above |

- `apps.perfMode` (`guide --perf-mode`), and `--perf-mode` on `ai worthiness` and `report app`: `generic`, `all` or a list of keys; the CLI takes them comma-joined (`energy,latency,throughput`).
- Selection = the registry metrics whose `selects` hold a chosen key (`dto/perf_mode.py`). Latency and throughput are one metric: one estimate, one ratio, shown in each selected unit, never two pieces of evidence.
- `generic` is the plain list of every key plus one flag on the resolved mode, `overall`: the decision rule and what is required differ from a hand-written list naming every key: generic requires no metric and judges on what was measured. Passes, labels and the renders see the list; `required` is empty, so a metric the harness cannot measure never stops it.
- A perfMode's name joins its keys in registry order with `+` (`latency+throughput+energy`), or is `generic`; `worthiness-<name>/` holds its verdicts.
- Selection filters the data, never the prompt: the evidence, the dossier and both renders carry only selected metrics, so a model never sees another.

## Verdict

| Mode | Improves when |
|---|---|
| any perfMode | at least one selected metric's ratio `to ÷ from` ≤ `improvingRatio` (0.97), and none ≥ 1 ÷ `improvingRatio` (1.031) |

- A pair is judged `improves`, `not_improving` or `not_measured`.
- `not_measured`: a selected metric has no ratio for the pair (not measured on a side, a zero median before, or energy of different kinds). A listed perfMode needs every selected metric; `generic` requires none and decides on the metrics that were measured, so a missing energy or allocation estimate never drops an option; one with no estimate at all is dropped, and a scope left with none is `no_evidence`, a current item never measured `current_not_measured`: the model never weighs an empty option.
- A selected metric without data is the static reason `no_evidence: <metric>`, logged; never a proxy and never `no_improvement`. Levels:

| Where | Unit judged | Without the metric |
|---|---|---|
| worthiness | a pair | the pair is `not_measured`; a group with no improving pair and such a pair is the static verdict `not_measured`, `no_evidence: <metric>`; the triage log counts them |
| dossier | an option | the option is dropped (a choice the model cannot weigh by the selection); a scope left none is `noOptions` `no_evidence: <metric>`, a static keep; the dossier step counts `noEvidence` |

- Why per option, not per scope: one option measured on every selected metric is still a fair choice; dropping the whole scope for another option's gap would hide it.
- Energy is never compared across kinds (`energy_kinds_differ`).
- Energy measurement: [docs/energy.md](../../../docs/energy.md). perfMode owns `run.metrics`, within what the harness can measure: [pipeline.md](pipeline.md) Device stage.

## Labels

`result/gain.py` holds the one rule, over `compare()`'s ratio and pImprove; `improvingRatio` comes from `criteria.yaml`.

| Per metric | When |
|---|---|
| `improved` | ratio ≤ `improvingRatio` and pImprove ≥ 0.95 |
| `worse` | ratio ≥ 1 ÷ `improvingRatio` and pImprove ≤ 0.05 |
| `unchanged` | otherwise; n < 2 is never beyond noise, so a single energy window stays here whatever its ratio |

| Overall (an option) | When |
|---|---|
| `improves` | a metric improved, none worse |
| `trade_off` | a metric improved and another worse |
| `worse` | a metric worse, none improved |
| `unchanged`, `not_measured` | no change beyond noise; no metric to label |

- Selected metrics only. `noise` per metric: `beyond`, `within`, `unknown` (n < 2).
- Shown as each option's `label` line in the site-replace and upgrade messages, and in the review sheet's facts.
- A zero median before keeps the option: it shows `no estimate: zero_median`, and the metric has no change.

## Confidence: pImprove

`pImprove` is the probability that the candidate's median is lower than the current one's. It grades a pair; it never rejects one. A pair under several selected metrics is graded by its improving metric with the highest pImprove.

| Level | pImprove |
|---|---|
| `ok` | ≥ 0.95 |
| `warn` | 0.80 to 0.95 |
| `weak` | < 0.80 |
| `too_few_runs` | either side has fewer than 2 runs; pImprove is `null`, never invented |

- Noise above 10% is acceptable; more runs or more processes are the remedy, not a stricter gate.
- Levels and `improvingRatio` live in `criteria.yaml`.

## Method

| Step | What |
|---|---|
| units | each metric keeps its runs per process (`Summary.processes`), read from the per-process `benchmark/process-N/benchmark.json` the manifest lists as `processes`; one process when there is none |
| resample | per draw: pick processes with replacement (when there are 2 or more), then inside each a circular moving-block resample of its runs, block length ⌈√n⌉ |
| statistic | the median of the pooled resample, for `from` and `to` in the same draw |
| pImprove | share of 2000 draws where `to` < `from`; a tie counts half |
| interval | the 2.5% and 97.5% bootstrap medians of one side (`Summary.low`, `high`); `null` below 2 runs |
| seed | fixed (1), so the same runs always give the same numbers |

- Why by process: runs within one process share JIT state, heap layout and clocks, so they are not independent. Concatenating processes hides the spread between them and makes intervals too narrow.
- Why blocks: the 50 runs of one process are autocorrelated (warm-up, thermal drift). Resampling single runs would treat them as independent.
- With 1 to 3 processes the process level has few distinct resamples; the blocks inside each keep the within-process spread.
- The merged `benchmark.json` must hold exactly the runs of the process files; a mismatch stops inbound.
