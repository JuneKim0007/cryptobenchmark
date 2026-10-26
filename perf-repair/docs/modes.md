# Modes

| Mode | Improves when | Proxy |
|---|---|---|
| `latency` | `to` median time per operation < `from` | no |
| `battery` | `to` median time per operation < `from`, and `to` allocations per operation ≤ `from` (unknown allocations, or `from` allocations 0: not improving) | yes |

- Worthiness reads no energy: time and allocations only.
- `repair replay --energy` reads `joulesPerOperation` from an `energy.json`.
- Every battery verdict carries `proxy: true`.
- Energy measurement: [docs/energy.md](../../docs/energy.md).
