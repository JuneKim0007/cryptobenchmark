# Algorithm catalogue

`catalog/algorithms/<family>_catalogue.yaml`, one per family of `catalog/families.yaml`, plus `common.yaml`; `catalog/algorithms.py` reads all of them through `DocumentKind` and refuses every catalogue on any bad entry (`algorithms_invalid`).

## Entry

Keyed by the algorithm id `<type>|<canonical>`, the canonical name of `catalog/algorithm-names.yaml`. `catalog/groups.yaml` lists the same ids per family.

| Field | Holds |
|---|---|
| `key` | `{type, source}`: the key the call takes, `none` without one |
| `required` | `{name, value, source}`: `parameters` (`none`, `iv`, `gcm`, `chacha`, `pbe`) and `nonce` (`none`, `unpredictable`, `unique`) |
| `optional` | arguments with what each changes; empty until measured |
| `conditions` | `output: {kind, bytes, source}`, `deterministic: {value, source}`, `authenticated: {value, source}` |
| `contract` | `{input, output}`: the components a swap must keep; absent when the name leaves one open, so it has no contract row |
| `sourcedOnly` | `{fact, value, source}`: `strengthBits` (bits, `{key}` or `{key, cap}` of a `keyStrength` map, null) and `minSdk` |
| `providers` | `<provider>: {<path>: <value>}`: only what differs; a path walks mappings by key and lists by `name` or `fact` |
| `provenance` | `{by: person}`, or `{by: agent, model, run, date}` |
| `aliases` | optional spellings |

- Every leaf's `source` is `measured`, `inferred` or a `common.yaml` source id; `strengthBits` may be `unsourced` and then null.
- The type facts (`key`, `parameters`, `nonce`, `output`, `deterministic`, `authenticated`, `strengthBits`, `minSdk`) come whole or not at all; `catalog/types.py` reads them as the rows of [change-classes.md](change-classes.md) Type.
- `common.yaml`: `sources`, `keyStrength` (SP 800-57 Part 1 r5 Table 2), `deterministicRelied`.

## Agent views (`catalog/views.py`)

| Function | Returns |
|---|---|
| `view_for(id, provider)` | the entry without `providers`, with only that provider's overrides applied; an unknown provider gets the base entry; an id in no or two catalogues is `algorithm_unknown` |
| `group_view(family)` | `{description, algorithms}`: the family's description and its ids |

## Static checks (`validation/catalogue_entry.py`)

An entry's form, its engine type against its family's, its id in exactly one catalogue and one group. Known gaps of the packaged catalogues: `SLH-DSA-SHA2-128S` and `XWING` in no group (not in `algorithm-names.yaml`).
