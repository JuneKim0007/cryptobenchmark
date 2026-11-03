# Used set

With `device.filterByApps` (default `true`) the guide hands probe_device the targets' detect, and the device stage runs in two passes, so the apps are scanned on today's probe before anything is measured:

```mermaid
flowchart LR
    P[pipeline.py --probe] --> S[screen: items, signatures, code-made groups] --> D[app step per target, static]
    D --> U[used.json] --> X[used-global.yaml: base + selection.exclude] --> B[pipeline.py --bench / --device]
    B --> I[inbound] --> S2[screen] --> U2[used.json again] --> T[primitives] --> G[guide grouping: pending in used.json only]
```

| step | rule |
|---|---|
| probe | `pipeline.py --probe` (`--device --probe` on a phone) when the plan reruns the probe; the benchmark run later reuses it on a host (`--discovery reuse`), a phone probes again |
| detect | each target's app step (`perfrepair.app`), no model; an app that fails here stops later at its own app step; the app step does not run twice |
| used | `used.json` ([artifacts.md](artifacts.md#usedjson)): what the sites resolve to, their groups' members, and for an item not yet grouped its candidates, so the benchmark already holds every option the model may later group it with; the model is asked after the benchmark |
| measured set | the used set joined with what device.yaml `benchmark.items` says was measured: a set grows, never shrinks, so a target removed keeps its rows |
| benchmark | reruns for the plan's reasons, or `<n> used items not measured`; a set that only shrank reruns nothing; a record without `benchmark` whose manifest is the base config's measured the whole base selection, nothing is missing |
| selection | `used-global.yaml`: the base `global.yaml`, its test set resolved, with one `selection.exclude` rule `{provider, type, name}` per device item outside the measured set; an item sharing its provider, type and canonical name with a kept one is never excluded; the base test set's includes, groups and overrides stay |
| probe digest | the manifest then carries the generated config's digest; device.yaml `benchmark.config` maps it back to the base digest, so the probe is judged by the base `global.yaml` |
| no item | no target reaches a device item: the base selection is measured, logged `device selection`, device.yaml records no `benchmark` |
| off | `false`: `used.json` removed, every askable item asked; a record with `benchmark` reruns the benchmark on the base config (`device.filterByApps off: ...`) |

- A changed set reruns the whole measured set, not only the new items: one session per comparison, since a group's members are compared with each other and the manifest holds one `benchmark.json`; cross-session drift (thermal state, frequency governor) would sit inside a ratio. The measured set is the apps' items, a small part of the device, so the rerun costs that part.
- A first run makes two pipeline runs (probe, then benchmark); later runs with the same targets make none.
- Logged: `device used` (`deviceItems`, `apps`, `sites`, `matched`, `used`, per `via`), `device selection` (`deviceItems`, `measured`, `excluded`), `device grouping` (`items` asked of, `asked`, `notUsed`).
- Each excluded item the base selection never held is one `exclude_matches_nothing` warning in `effective.yaml`: harmless, and the price of not repeating cryptobenchmark's include matching here.

## Evidence

API 30 emulator capture, grouping rebuilt at profiles schema 4, the apps' `sites.json` resolved on that device, grouping from empty:

| targets | used set (site, group, candidate) | runnable | asked of 46 askable | notUsed | cases of the 100 the base run measured |
|---|---|---|---|---|---|
| none: filter off | 275 | 155 | 46 | 0 | 100 |
| threema | 18 (5, 13, 0) | 14 | 0 | 46 | 36 |
| threema, deltachat, DankChat | 41 (11, 24, 6) | 30 | 8 | 38 | 70 |
| 42 apps with JCA sites (43 folders) | 62 (18, 32, 12) | 44 | 16 | 30 | 72 |

- Dry-run grouping in that order on one folder: 0, then 8, then 16 model calls in total; each new set asked only what it added; the 43-folder set was then 56 items, since an item with a record brings its group, not its candidates.
- The base run there was `testsets/quick.yaml` (20 items); against a full-device test set the measured items fall from 155 runnable to 14, 30 and 44.
- Host check (`config/global-demo.yaml`, the demo app): used set 6 of 214 items, 208 exclude rules, the 3 smoke cases measured; the second run reused every stage and made no pipeline run.
