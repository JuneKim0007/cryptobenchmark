# Replacement

From an app's source to a measured before/after of each call site the model chose to replace. Types: `src/perfrepair/dto/site.py`.

## Flow

| step | who | reads | writes |
|---|---|---|---|
| detect | static | app root, the run's probe | `apps/<app>/sites.json` |
| scope | static | sites, app source | `apps/<app>/scopes.json` (`Scope` per site: function span, sinks, key source) |
| dossier | static | scopes, `grouping/groups.json`, `measurements.json` | `apps/<app>/dossiers.json` (`Dossier`: function source, current item, `Option`s with `Estimate`s) |
| replace | model | one `Dossier` per conversation | `apps/<app>/replace/` outbox, `replacements.json` (`Replacement`) |
| edit | static | replacements, app source | `apps/<app>/patched/` (a copy; the app is never edited), `edits.json` |
| harness | static | scopes, the original and patched function | `apps/<app>/harness.yaml` for cryptobenchmark |
| measure | device | `harness.yaml` | before/after `benchmark.json` per scope: `timeNs`, `allocationCount`, energy |
| report | static | measurements | `apps/<app>/report.json`, `report.md`; `apps/summary.md` across apps |

## Contracts

- A scope's `id` is `scope_id(app, file, function, line, call)`, so rerunning detection and scoping on the same source gives the same ids, and every later step refers to a scope only by id.
- An `Option` is a member of the site's group that is available in the app's process, from the platform or bundled by the app. Its `pins` are the parameters that make the swap like-for-like (IV length, tag length, OAEP digests).
- An `Estimate` is graded, never a gate: `pImprove` is the probability the option is better on that metric. Below 0.95 the report says `warn` with the number.
- The model picks one option or `keep`, and expresses the change only as `Edit`s of a kind in `EDIT_KINDS`. Static code renders and applies them. A replacement whose edits do not apply, do not compile in the harness, or fail the interop check (data from before the swap must still decrypt after it) is reported as `rejected` with the reason, and is never measured.
- `harness.yaml` names each scope's original and patched function source and its inputs. cryptobenchmark compiles both into the benchmark app and measures them like any other case.
