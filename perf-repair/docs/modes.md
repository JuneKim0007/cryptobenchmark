# Modes

Criteria are data: `src/perfrepair/result/criteria.yaml`. A mode differs only in its entry there.

| Mode | Improves when | Proxy |
|---|---|---|
| `latency` | time ratio `to ÷ from` ≤ `improvingRatio` (0.97) | no |
| `battery` | time ratio ≤ 0.97, and `to` allocations per operation ≤ `from` (`allocationsMustNotRise`) | yes |

- A pair is judged `improves`, `not_improving` or `not_measured`.
- `not_measured`: time improves but a criterion's data is missing (allocations unknown, or `from` allocations 0). It is never reported as `no_improvement`.
- Worthiness reads no energy: time and allocations only.
- `repair replay --energy` reads `joulesPerOperation` from an `energy.json`.
- Every battery verdict carries `proxy: true`.
- Energy measurement: [docs/energy.md](../../docs/energy.md).

## Confidence: pImprove

`pImprove` is the probability that the candidate's median is lower than the current one's. It grades a pair; it never rejects one.

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
