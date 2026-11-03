# Modes

A decision's mode is its perfMode: which registry metrics (`src/perfrepair/dto/metrics.py`) it is given and judged by. The rule and its threshold are data: `src/perfrepair/result/criteria.yaml`.

## perfMode

| Key | Selects | Shown as |
|---|---|---|
| `latency` | `timeNs` | ms/op by default (`analysis.units.latency`) |
| `throughput` | `timeNs` | MB/s by default (`analysis.units.throughput`); MB/s and MiB/s only where an input size exists |
| `memAlloc` | `allocationCount` | allocations/op |
| `energy` | `energyJ` | J/op, with its kind |
| `generic` | every metric | every unit above |

- `apps.perfMode` (`guide --perf-mode`), and `--perf-mode` on `ai worthiness` and `report app`: `generic` or a list of keys; the CLI takes them comma-joined (`energy,latency,throughput`).
- Selection = the registry metrics whose `selects` hold a chosen key (`dto/perf_mode.py`). Latency and throughput are one metric: one estimate, one ratio, shown in each selected unit, never two pieces of evidence.
- A perfMode's name joins its keys in registry order with `+` (`latency+throughput+energy`); `worthiness-<name>/` holds its verdicts.
- Selection filters the data, never the prompt: the evidence, the dossier and both renders carry only selected metrics, so a model never sees another. The report still shows people every measured metric, marking the selected ones.

## Verdict

| Mode | Improves when |
|---|---|
| any perfMode | at least one selected metric's ratio `to ÷ from` ≤ `improvingRatio` (0.97), and none ≥ 1 ÷ `improvingRatio` (1.031) |

- A pair is judged `improves`, `not_improving` or `not_measured`.
- `not_measured`: a selected metric has no ratio for the pair (not measured on a side, a zero median before, or energy of different kinds). A listed perfMode needs every selected metric; `generic` decides on the metrics measured and names the rest.
- A selected metric without data is the static reason `no_evidence: <metric>`, logged; never a proxy and never `no_improvement`. Levels:

| Where | Unit judged | Without the metric |
|---|---|---|
| worthiness | a pair | the pair is `not_measured`; a group with no improving pair and such a pair is the static verdict `not_measured`, `no_evidence: <metric>`; the triage log counts them |
| dossier | an option | the option is dropped (a choice the model cannot weigh by the selection); a scope left none is `noOptions` `no_evidence: <metric>`, a static keep; the dossier step counts `noEvidence` |

- Why per option, not per scope: one option measured on every selected metric is still a fair choice; dropping the whole scope for another option's gap would hide it.
- Energy is never compared across kinds (`energy_kinds_differ`).
- Energy measurement: [docs/energy.md](../../docs/energy.md). The device stage checks the run config measures what the perfMode selects: [pipeline.md](pipeline.md) Device stage.

## Confidence: pImprove

`pImprove` is the probability that the candidate's median is lower than the current one's. It grades a pair; it never rejects one. A pair under several selected metrics is graded by its improving metric with the highest pImprove.

| Level | pImprove |
|---|---|
| `ok` | ≥ 0.95 |
| `warn` | 0.80 to 0.95 |
| `weak` | < 0.80 |
| `too_few_runs` | either side has fewer than 2 runs; pImprove is `null`, never invented |

- A report reads "improved, 83% (warn)". Noise above 10% is acceptable; more runs or more processes are the remedy, not a stricter gate.
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
- Before this method, the interval was an order-statistic interval labelled 95% that fell back to min..max at n ≤ 5 (real coverage 50 to 94%) and had zero width at n = 1.
- The merged `benchmark.json` must hold exactly the runs of the process files; a mismatch stops inbound.
