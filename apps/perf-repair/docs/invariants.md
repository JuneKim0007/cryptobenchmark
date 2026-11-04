# Invariants

## Finding

| Field | Holds |
|---|---|
| `invariant` | the rule's id below |
| `severity` | `blocking`: the artifact is wrong and the replace step would act on it; `advisory`: a recorded state or a judgement a person or the model makes; `undecided`: the artifacts or the source do not decide the rule |
| `subject` | `group <id>`, `scope <id>`, `unit <id>`, `<app> scope <id>`, or the two items compared |
| `evidence` | `file:line` in the app's project root, or `group <id>`, with what was read there |
| `fix` | what to change or rerun |

- Command: `python3 -m perfrepair.validation.invariants <device> [--apps <folder>] [--against <device>] [--json <file>]`; one line per finding, a count per invariant, exit 1 on any `blocking`.
- Guide: before an app's `replace` step, a `blocking` finding of its own scopes or of a group its dossiers draw from stops with `invariant_failed`; advisory and undecided ones are only printed by the command.
- `--apps`: the folder that holds the app trees, when app.json `root` has moved; without a readable source a scoping rule is `undecided`.

## Grouping

Read from `grouping/groups.json`, `profiles.json`, `checks.json`, `screen.json` and each app's `dossiers.json`.

| Invariant | Severity | Fails when |
|---|---|---|
| `key_contract_agrees` | blocking | a group of two or more holds `app_held` and `provider_held` members (`checks.json` `key_contract_differs`), or a member whose signature `key` component is `unknown`: nothing recorded whether its key leaves the provider; a group whose every member is `broken` or `platform_deprecated` and which no dossier offers is exempt |
| `signature_agrees` | blocking | two members know different values of one signature component (`known` or `convention`), or `checks.json` holds `resolved_parameters_differ` for the group |
| `no_runnable_no_options` | blocking | a dossier option names a member of a group with no runnable member |
| `interop_not_run` | advisory | a group with two or more runnable members while `interop.status` is `not_run` |
| `algorithm_split` | advisory | one canonical name of `screen.json` in several groups of a family, with members of equal screen status, key contract and signature in each |
| `grouping_stable` | blocking | with `--against`: two items whose key contract, key kind, runs and signature are equal in both runs are together in one run and apart in the other |

- A screened-out item is still an option of its own algorithm (`lowers_status`, `dto/screen.py`), so a screened-out group a dossier offers stays under `key_contract_agrees`: its swap is a real one.
- A failed interop pair is never an option: `validation/dossiers/dossier.py` refuses it; no invariant repeats it.
- `algorithm_split` is advisory: a false split loses options and joins nothing wrong; whether to merge is the model's call.

## Scoping

Read from each app's `scopes.json` and `units.json` against the source under app.json `root` and `projectRoot`; `held_in_field_setup_once` also reads the device's `rows.json`.

| Invariant | Severity | Fails when |
|---|---|---|
| `site_line_holds_call` | blocking | the cited line does not start the recorded `call` (whitespace ignored, the call may run on over its lines) |
| `held_in_field_setup_once` | blocking | a `held_in_field` scope's use one method away sits in a function that calls the factory of the engine type, or the engine's configuration on the same receiver; a configuration call is accepted when every `fixed` row of the scope's type and algorithm in `rows.json` has `perCall` `initAndOperation`: that variant measures a re-init per call, so the pattern is right |
| `created_per_call_one_function` | blocking | a `created_per_call` scope's use line holds no call of that name, or no use is inside the function around the site |
| `inverse_link_sides` | blocking | the operations read from an `inverse` link's step lines (`scope/engines.yaml` operations, `scope/units/relations.yaml` steps) are not inverses in `relations.yaml` |

- `undecided`: no readable source, no function around a line, a use call with no single receiver, an operation no step line spells out.

## Known-answer fixtures

- `tests/fixtures/scoping/`: own-written Java and Kotlin sources, one site per pattern reason and link kind, and the hard cases: a lazy cache in a field, a re-init per call on a held object, a held object whose fixed variant inits per call, an escaping object; `expected.yaml` holds the true reading of each.
- `validation/scoping/accuracy.py` runs the scoper over them and counts, per rule, the sites it reads right; a wrong reading is listed, never tuned away.
