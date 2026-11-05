# Change classes

## Diagram

```mermaid
flowchart TD
    C[scope's current item] --> G[other members of its group]
    C --> F[other canonical names of its family, catalog/types.yaml]
    G --> D[drop-in: every contract equal]
    F --> R{floor, properties, nonce, availability, measured, screening}
    R -- any fails --> X[rejected with every reason]
    R -- all pass --> P[pair diff]
    P --> L[local-edit]
    P --> M[migration]
    D --> O{class up to apps.maxChange}
    L --> O
    M --> O
    O -- yes --> A[option: the model selects, gate C checks]
    O -- no --> N[notOffered: recommendation in report.json and summary.json, never applied]
    X --> N
```

## Type

`catalog/types.yaml`, per family and canonical name, each fact sourced; `catalog/types.py` refuses the whole file on any bad row.

| Field | Values |
|---|---|
| `outputKind` | `digest`, `tag`, `ciphertext`, `aead_ciphertext`, `signature`, `shared_secret`, `secret_key`, `key_pair` |
| `authenticated`, `deterministic` | true, false |
| `nonceRequired` | `none`, `unpredictable` (a fresh random IV each call), `unique` (never repeated under one key) |
| `parameters` | the shape of the parameter object the call passes: `none`, `iv`, `gcm`, ... |
| `outputBytes` | bytes, null when it varies |
| `keyType` | the key the call takes, `none` without one |
| `strengthBits` | bits, `{key: <map>}` read at the key size, `{key, cap}` for the lower of the two, null unknown; SP 800-57 Part 1 r5 Tables 2 and 3 |
| `minSdk` | the first Android API level of the open-ended range on the reference page; null: check the device |

- Type is family + `outputKind` + properties; a model never decides it.

## Pair diff

| Field | Value | When |
|---|---|---|
| `input` | `same` | the parameter shape is equal |
| | `reshaped` | the shape differs and `parameters`' settled origin is `generated`, `literal` or `derived`, or the candidate takes none |
| | `new_parameter` | otherwise, and whenever the current call passes none |
| `key` | `same`, `size`, `type` | `keyType` equal and one key-size fact; another key-size fact; another `keyType` |
| `output` | `bytes` | same `outputKind`, other bytes or length |
| | `kind` | another `outputKind` |
| `reach` | `local`, `return`, `unknown`, `persist` | the sinks are all `local`; all `local` or `return`; a sink `unknown` or the lifecycle's `binding` `field` (the object outlives the function); any other sink |
| `addsDependency` | true | the candidate's provider is one `providers.bundled` installed and the app does not ship |

`same` output is a drop-in's: a drop-in carries no diff.

## Classes

| Class | Holds when |
|---|---|
| `drop-in` | the candidate is another member of the current item's group |
| `migration` | `addsDependency`, `reach` `persist` or `unknown`, `key` `type`, `key` `size` with a key not generated in the function, `input` `new_parameter`, or `output` `kind` |
| `local-edit` | none of the above |
| `rejected` | any reason below |

| Reject reason | Holds when |
|---|---|
| `type_unknown` | no row for the current item or the candidate |
| `strength_below` | the candidate's strength at the scope's key size is below the current one's |
| `strength_unknown` | the two strength facts differ and either has no value at this key size |
| `authenticated_lost` | the current is authenticated, the candidate is not |
| `deterministic_lost` | the current is deterministic, the candidate is not, and the output kind is in `deterministicRelied` |
| `nonce_not_generated` | both need a nonce, the requirement differs, and `parameters`' settled origin is not `generated` |
| `unavailable` | the app's `minSdk` is below the candidate's and its provider is not bundled |
| `availability_unknown` | the candidate's `minSdk` is null, or above API 1 with the app's unread, and its provider is not bundled |
| `not_measured` | it does not run, its provider is absent, or `rows.json` has no line of it |
| `deprecated` | screening refuses it for this app (`refused_target`), or a broken current's candidate is not `accepted` |
| `same_engine` | a member of the current item's group from its own provider under the same canonical name (`AES/...` and `AES_128/...`): one engine, no signal to measure, and the key size that tells them apart is never known at the site; kept in `notOffered`, never offered |
| `not_listed` | a broken current's accepted candidate the upgrade list leaves out while it has a measured target |
| `no_gain` | of a current that is not broken, of any class: one estimate proven worse (ratio at or above `1 / improvingRatio`, `pImprove` at or below 1 minus the top level's floor, `result/criteria.yaml`) and no estimate at or below `improvingRatio`; an estimate with `pImprove` null proves nothing and saves nothing unless its ratio improves |

- Every reason found is listed, not the first.
- A candidate of the current item's canonical name is left to grouping: it is a drop-in or nothing.
- A group member from a provider outside the app's process is not a drop-in: `migration`, `output` `same`, `addsDependency`.

## Availability

- The same rule is the provider path's: a provider the harness bundled is the app's own only when the app ships its library.
- A provider is in the app's process when the probe's `origin` is not `bundled`, the app's `app.json` `bundled` names it, or the probe's `artifact` group:name is one the app ships.
- A capture without `origin` reads as all platform.

## Two tracks

The deliverable is a recommendation study and, apart from it, the provider path; an option's `track` says which.

| `track` | Holds when | Means |
|---|---|---|
| `provider_path` | a drop-in, the same canonical name, from another provider, and both the provider the site is on and the one offered are in the app's process (Availability) | the same output from another implementation the app already has; the only track a swap is applied as |
| `recommendation` | any other option | a swap and what would have to change; deliberately loose, never claimed as an app improvement |

- The provider a site is on (`result/provider_path.py`): the one it names; a name the app ships and the harness measures under its alias (`app.json` `bundled`, the probe's `artifact`) is that alias's item; a `default` site in an app that inserts a provider it ships at position 1 (`registers` `call`, `position`, matched to `catalog/bundled-providers.yaml` `create`) is on that provider's item when it registers the name, so the platform member is its provider path back; any `default` site's options carry `resolved_by_order`.
- A same-canonical member from the current item's own provider is `same_engine`, never an option; a group of nothing else plans no interop pair.

## Review facts

Every option carries three fields code computes; the model is not asked for them and no option is called safe by them.

| Field | Value |
|---|---|
| `outputChanges` | true when the pair diff's `output` is not `same`: every class but a drop-in and a group member only the harness has |
| `reach` | the scope's reach, as in the pair diff |
| `needsReview` | the facts below that hold, in this order; empty when the output stays the same, but for `adds_dependency` |

| `needsReview` | Holds when the output changes and |
|---|---|
| `reach_local_unverified`, `reach_return_unverified`, `reach_unknown`, `reach_persist` | its reach: `local` is a pattern reading (17 of 29 audited `local` sinks were wrong), and a returned value's callers are not read |
| `field_bound` | the lifecycle's binding is `field` |
| `output_length_changes` | another output kind, an output length of null on either side, or two lengths |
| `key_changes` | the diff's `key` is not `same` |
| `key_size_unknown` | the current item takes a key and the scope's key size is unknown |
| `parameter_changes` | the diff's `input` is not `same` |
| `adds_dependency` | the candidate's provider is the harness's, not the app's (any output) |
| `resolved_by_order` | the site's provider is the default order's (any output, any track) |

- A recommendation stays a recommendation: `return` and `local` reach stay `local-edit`, offered up to `apps.maxChange`, deliberately loose; `needsReview` says what a person checks before it means anything for the app.

## `apps.maxChange`

| Value | Offered |
|---|---|
| `drop-in` | group members; every other class goes to `notOffered` |
| `local-edit` | also `local-edit` candidates |
| `migration` | also `migration` candidates |

- An option above `drop-in` carries `change` and `diff`; the model is shown them and selects; it never adds a candidate.
- A dossier that gains no option under a higher `maxChange` is byte-equal; one that gains an option is a new evidence digest, stale until `--refresh`.
- `edit` applies `set_algorithm` and `pin_parameters` only: an option whose `input` is `reshaped` still needs its parameter built by the function.
