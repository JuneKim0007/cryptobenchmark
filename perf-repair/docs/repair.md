# Repair

Command: `python3 -m perfrepair.repair <step>`; every step but replay takes `--run <run> --app-name <app>` and writes under `<run>/repair/<app>/`.

| Step | Flags | Input | Output |
|---|---|---|---|
| candidates | `--sites` | an app's `apps/<app>/sites.json`, `grouping/groups.json` | `candidates.json`: sites resolved `default` or `explicit` |
| test-set | `-o` | candidates | YAML test set at `-o`: items the app runs and their alternatives |
| choose | `--mode` (default `latency`) | candidates, `worthiness-<mode>/verdicts.json` | `choices.json`: replacement or none, with the reason |
| patch | `--app` | choices, the app tree | `patches.json`, validated by `validation/repair.py` |
| replay | `--benchmark`, `--energy`, `--before`, `--after` (`Type\|name\|provider`), `--input` | a `benchmark.json` (+ `energy.json`) | YAML on stdout: before, after, `speedup`, `energyRatio` |

## Limits

| Limit | Rule |
|---|---|
| patch | literal arguments on one line; a call built from variables is skipped |
| replay | times the call's primitive at one input size in the benchmark harness, not the app running |
| default provider | the first by precedence that registers the name |
| provider rejecting the key at `init` | not skipped |
| Cipher transformation served only through its base service | not resolved |
