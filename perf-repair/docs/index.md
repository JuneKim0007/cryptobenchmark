# Docs

```
docs/artifacts.md : device folder artifacts: producer, consumers, validator; manifest fields; run log statuses
docs/change-classes.md : a candidate beyond the group: type, floor, availability, pair diff, change class, reject reasons, apps.maxChange
docs/decisions.md : the engine's retry and model defaults; the worthiness decision: input, answer, gate, fallback; static triage
docs/grouping.md : grouping stage: files, answer contract, gates, families, findings
docs/limits.md : what the measurements and the app scan cannot answer
docs/modes.md : perfMode: the selected metrics, the one verdict rule, no_evidence; pImprove, its levels and the bootstrap method
docs/pipeline.md : stages, commands, and what each reads and writes
docs/repair.md : call sites to before/after: steps, inputs, outputs, limits
docs/replacement.md : app source to measured before/after per replaced call site: flow, files, contracts
docs/run-log.md : <device>/log/: events.jsonl, its views (status, model stages, bugs), pipeline transcripts, status line kinds, watch and log summary
docs/screening.md : screening statuses, precedence, lookup, catalog settings and identity, the model review of unknown items, the screening.yaml sections, loader codes, sources policy, limits
docs/settings.md : perfrepair.yaml and .env: lookup, precedence, keys, roles, errors
docs/shared-functions.md : functions three or more modules import: module, signature, rule, callers
docs/signature.md : what code reads per item, per engine type; known, convention, unknown; which items it groups
docs/stops.md : every stop, warn and skip code: default action, overridable or fixed, exit, next step; terminate, Halt, stops.<code>
docs/used-set.md : device.filterByApps: the two-pass device stage, used.json, the measured set and its selection, the numbers on the API 30 capture
```
