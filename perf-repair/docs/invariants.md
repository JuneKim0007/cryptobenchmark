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
- `--apps`: the folder that holds the app trees, when app.json `root` has moved; without a readable source a scoping rule is `undecided`.

## Grouping

Read from `grouping/groups.json`, `profiles.json`, `checks.json`, `screen.json` and each app's `dossiers.json`.

| Invariant | Severity | Fails when |
|---|---|---|
| `key_contract_agrees` | blocking | a group of two or more holds `app_held` and `provider_held` members (`checks.json` `key_contract_differs`), or a member whose signature `key` component is `unknown`: nothing recorded whether its key leaves the provider |
| `signature_agrees` | blocking | two members know different values of one signature component (`known` or `convention`), or `checks.json` holds `resolved_parameters_differ` for the group |
| `no_runnable_no_options` | blocking | a dossier option names a member of a group with no runnable member |
| `interop_not_run` | advisory | a group with two or more runnable members while `interop.status` is `not_run` |
| `algorithm_split` | advisory | one canonical name of `screen.json` in several groups of a family, with members of equal screen status, key contract and signature in each |
| `grouping_stable` | blocking | with `--against`: two items whose key contract, key kind, runs and signature are equal in both runs are together in one run and apart in the other |

- A failed interop pair is never an option: `validation/dossiers/dossier.py` refuses it; no invariant repeats it.
- `algorithm_split` is advisory: a false split loses options and joins nothing wrong; whether to merge is the model's call.

## Scoping

Read from each app's `scopes.json` and `units.json` against the source under app.json `root` and `projectRoot`.

| Invariant | Severity | Fails when |
|---|---|---|
| `site_line_holds_call` | blocking | the cited line does not start the recorded `call` (whitespace ignored, the call may run on over its lines) |
| `held_in_field_setup_once` | blocking | a `held_in_field` scope's use one method away sits in a function that calls the engine's configuration on the same receiver, or the factory of the engine type |
| `created_per_call_one_function` | blocking | a `created_per_call` scope's use line holds no call of that name, or no use is inside the function around the site |
| `inverse_link_sides` | blocking | the operations read from an `inverse` link's step lines (`scope/engines.yaml` operations, `scope/units/relations.yaml` steps) are not inverses in `relations.yaml` |

- `undecided`: no readable source, no function around a line, a use call with no single receiver, an operation no step line spells out.
