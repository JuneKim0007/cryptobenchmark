# Repair upgrade

Role `apps.upgrade`, kind `repair-upgrade`, prompt `repair/upgrade`, its own charter: a change here leaves `suggest/site-replace` and its saved decisions alone.

| field | repair-upgrade |
|---|---|
| item | one unlisted `upgrades` row of `<app>/dossiers.json` |
| message | the site, sinks and reach, the current and screening's reason, the options best first: change, own medians, any ratio; no function source |
| answer | `option` alias, `reason`; no answer keeps the current; gate C: `validation/upgrade.py`, resolved to the item |
| no model | a row the list identifies takes its first ranked target, source `list` |
| dropped item | `needs_migration`, needs `model_dropped`, source `fallback`; never an automatic edit |
| state | `<app>/upgrades.json`: `{schemaVersion, app, upgrades}`, each `{scope, current, status, option, source, reason, edits, needs, review}`; also what `no_secure_option` and `not_reached` broken uses became |
| outbox | the charter's inputs hash the asked items, so a changed candidate list opens a new outbox and an answer never outlives what it saw |

| status | holds when |
|---|---|
| `upgraded` | none below: `edits` (`set_provider`, `set_algorithm`, `pin_parameters`, what differs) reach `edit` as a `replace` over replace's static keep |
| `needs_migration` | `needs` holds any of: `persisted_data`, `wire_format`, `unknown_sink` from the scope's sinks; `linked_members` (a unit of more than one: the others must follow); `provider_held_key`; `parameters_unknown`; `reach_return_unverified` (below); `reach_persist`, `reach_unknown`, `field_bound`, `key_changes`, `parameter_changes`, `adds_dependency` from the option; a member's reject reason under `person_judges` (below), with no `option`; else `migration` for its class |
| `no_secure_option` | the family has no accepted, measured member; a report line, the run goes on |
| `not_reached` | another `noOptions` reason came first, named in `reason` |

- Code decides edit or person from these facts; the model's risk list plays no part. A `return` reach is a person's: its callers are not read, and a caller may store the value (threema `calcVerification` is stored and compared later). Only the lifecycle's `outputCompared` lifts it: the function reads its outputs only to compare them with each other and keeps none (`scope/lifecycle/output.py`).
- A `local` reach stays an edit, with `reach_local_unverified` in `review`: `sinks` are patterns over the body, so a store they do not name reads `local`.
- `person_judges: <reasons>` in `noOptions`: every accepted, measured member is refused by a reject reason, such as `deterministic_lost` or `strength_unknown`; the row's `needs` are those reasons.
- An upgrade's swap gets no `same_output` check: `harness.yaml` marks it `upgrade: true`, the plan records `output_changes` and the scope is measured unchecked. A partner in the harness keeps `round_trip`, each side on its own variant's artifact.
