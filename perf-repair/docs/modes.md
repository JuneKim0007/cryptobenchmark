# Modes

| Mode | Improves when | Proxy |
|---|---|---|
| `latency` | `to` median time per operation < `from` | no |
| `battery` | `to` median time per operation < `from`, and `to` allocations per operation ≤ `from` (unknown allocations: not improving) | yes |

- No energy is measured: cryptobenchmark records time and allocations; CPU counters fail on the emulator.
- Every battery verdict carries `proxy: true`.
- Energy per operation is measurable on Pixel Tensor devices through ODPM rails in a Perfetto trace (GOMES).
