# Algorithm catalogue

`catalog/algorithms/<family>_catalogue.yaml`, one per family of `catalog/families.yaml`, plus `common.yaml`, `recipes.yaml` and `deviations.yaml`; `catalog/algorithms.py` reads all of them through `DocumentKind` and refuses every catalogue on any bad entry (`algorithms_invalid`).

## Entry

Keyed by the algorithm id `<type>|<canonical>`, the canonical name of `catalog/algorithm-names.yaml`. Spellings live only there, never in an entry. `catalog/groups.yaml` lists the same ids per family, with exemplars per group. Every key and value is defined in `catalog/glossary.yaml`.

| Field | Holds |
|---|---|
| `key` | `{type, bytes, origin, source}`: the key algorithm, accepted secret key lengths, and `origin` (`app`, `provider`, `password`, `none`) |
| `required` | rows `{name, recipe, bytes, value, rule, use, passedTo, sameGroupAs, source}`: `name` is a role of the glossary's `algorithm.role`, which says how a value is made (`make`) and how long it lives (`lives`, one word or one per direction); `recipe` names the recipe of `recipes.yaml` that makes the object carrying it, and the rows naming one recipe go to their call as one object; an argument the call fails without, tested by leaving it out; absence means not needed. A key agreement states its private key and the peer's public key (`doPhase`, `sameGroupAs: privateKey`); a signature a private key to sign and a public key to verify; a keyed cipher or MAC its key length; a digest only its input; a wrap the key it wraps (`passedTo: wrap`); a KEM its recipient's public key. A size is given as the call takes it: `keySize` `value` in bits, `secretKey` `bytes`. `use: decrypt`: encrypting runs without it because the provider generates one. `rule`: `unpredictable` or `unique` for an IV or nonce |
| `optional` | `{name, accepted, default, affects, source}`: what may be given and what each changes |
| `conditions` | `output: {kind, bytes, formula, bits, source}`, `deterministic: {value, source}` (`always`, `fixedParameters`, `never`), `authenticated: {value, source}`; where stated `input`, `reuseRefused`, `roundTrip`, `wrapOnly`, `spellingRuns` (a spelling of the id that is another service on that build) |
| `lifecycle` | `{reset: {forward: {value, source}, reverse: {value, source}}}`, the directions the entry's operations run: `afterInit` when one operation leaves the engine in its post-init state, `none` when it needs a new init, as a GCM encrypt does and a GCM decrypt does not; a `measured` reset is the requirement probe's `facts.reset` ([requirements.md](../../benchmark/modules/environment/discovery/docs/requirements.md) reset), `resets: true` read as `afterInit`, a refusal as `none`; `reinit` is derived per operation of a build's view, never stored: a forward operation (`operations.directions`) is `perUse` when a role that lives perUse going forward has a required or optional row, whatever its `use`; a reverse operation is `never`, its value `copied` |
| `operations` | `{value, source}`: the operations the entry supports and the harness times |
| `contract` | `{key, input, output}`: `key` is `app`, `provider`, `password` or `none` (a `none` or `password` row has no `.p` variant); `input` and `output` the components a swap must keep, each a value or `{value, assumed: true}` for a provider convention nothing recorded confirms (rows compare `value`; the description shows `(assumed)`); absent when the name leaves one open, so it has no contract row |
| `sourcedOnly` | `{fact, value, source, url}`: `strengthBits` (bits, `{key}` or `{key, cap}` of a `keyStrength` map, null) and `minSdk` |
| `providers` | `"<name> @ <build>": {<path>: <value>}`: what differs for that one provider build and no shared fact states, and where the entry says otherwise than one; a path walks mappings by key and lists by `name` or `fact`; `required.<name>` or `optional.<name>` is a whole row, null when that build runs without it |
| `provenance` | `{by: person}`, or `{by: agent, model, run, date}` |

- Every leaf's `source` is `measured`, `sourced` (with its `url`) or `inferred`. `measured`: a run varied or observed that very value on that build; a value merely not refuted is `inferred`. The label is a statement about a run outside this repository: no repo check or CI job enforces it, and a changed measured value passes `catalogue_check`. A null fact is never `sourced`. A row's one `source` does not cover its `rule` or `affects`.
- A base value holds for every build that observed it, except a value set by a stated ground, never by count: key custody (a keystore build's `key.origin`, `contract.key`), a spelling that is another service (the Conscrypt `PBEWithHmac*` alias), a standard's statement (`deterministic` sourced to FIPS 204 or 205 where a build shows it), a measured reset, since every direction's base holds one (a Conscrypt GCM-SIV encrypt refuses a second doFinal, BC on API 26 runs a second GCM encrypt). Elsewhere, where builds disagree the base has none and each observing build carries its own under `providers`, a whole condition `{value, source}` or row, null when it runs without the row; never a value chosen by counting builds. `catalog/types.py` then reads a type property as holding only when it holds on every build.
- A build key is `catalog/provider-builds.yaml`'s: a platform provider `@ android-<sdkInt>`, a bundled copy `@ <artifact>`, a host provider `@ jdk-<version>`; the provider's own version string stands beside it as `selfReported`, since it does not identify a build. `catalog/provider_builds.py` reads the file, `build_key` makes a key from what a probe records, a catalogue key outside the file is refused at load.
- The type facts (`key`, `output`, `deterministic`, `authenticated`, `strengthBits`, `minSdk`) come whole or not at all; `catalog/types.py` reads them as the rows of [change-classes.md](change-classes.md) Type. The parameter shape and nonce kind it reads from the `required` rows' `recipe` and `rule`.
- `common.yaml`: `sources` (every url a catalogue cites, by id), `keyStrength` (SP 800-57 Part 1 r5 Table 2), `deterministicRelied`.
- `recipes.yaml`, read by `catalog/recipes.py` (`recipes_invalid`): each recipe by id in one form, tried in order: `class` + `args` (a public constructor), `factory` + `steps` (a static method or builder class), `builder` (a function a person wrote in the harness; an agent may name one, never write one). An argument holds `kind` (`bytes`, `int`, `string`, `enum`, `keyRef`, `recipe`, `constant`) and the `role` it passes, or the `value` of a constant.

## Facts stated once

Two forms hold what many entries would otherwise copy. Reading applies them, so an entry's `raw["providers"]` and `view_for` see every build's differences: a behaviour, then a deviation, then the entry's own.

| Form | File | Holds |
|---|---|---|
| Provider behaviour | `catalog/provider-builds.yaml` `providers.<name>` | `behaviour: {<path>: <value>}`, true of every id the provider registers, and `registers`, rows of `builds` and `names` saying which ids on which builds; a path whose parent the entry does not hold is skipped; the entry says otherwise under its own `providers` (the 8 RSA ciphers keystore-born only on API 26 and 30) |
| Deviation | `catalog/algorithms/deviations.yaml` | by id `<subject>.<fact>`: `fact` in words, `builds` (a build key, or a provider name for all its builds), `names`, `set: {<path>: <value>}` |

`catalog/deviations.py` reads the file (`deviations_invalid`). A name no catalogue holds, and two deviations stating one path of one name on one build, are refused at load.

## Glossary (`catalog/glossary.py`)

`catalog/glossary.yaml` is a tree: `group` holds the words of `groups.yaml`, `algorithm` the words of the catalogues, `recipe` those of `recipes.yaml`, `plan` those of the build plans, `deviation` those of `deviations.yaml`, `build` those of `provider-builds.yaml`, `names` those of `algorithm-names.yaml`, nested by their real structure. A term holds `means` and either closed `values` or an open `format` (number, url, text, algorithmId, requiredName, boolean, role, recipeId, className, deviationId, operation, outputFormula); `unused` says why a listed value, or the term, nothing holds yet stays; `derived` marks a term computed and never stored, refused in a catalogue.

| Function | Returns |
|---|---|
| `what_is(path)` | that term or subtree: `what_is("algorithm.required")`, `what_is("group")` |
| `what_is(path, value)` | the value's one meaning: `what_is("algorithm.required.name", "peerPublicKey")`; an unknown key or value is `glossary_unknown`, naming the valid ones |

`tests/test_glossary.py` closes the catalogues, `recipes.yaml`, `deviations.yaml`, `groups.yaml`, `provider-builds.yaml` and `algorithm-names.yaml` over the tree; the last two are refused at load. A role's `goesTo` lists the calls a required row of it may name per engine type; `output.bytes` is null on generators and agreements and, when stated, what `formula` fixes.

## Agent views (`catalog/views.py`)

| Function | Returns |
|---|---|
| `view_for(id, provider=None)` | the entry without `providers`, with only that build's overrides applied (`provider` is a build key, or a name one build carries such as `BundledBC`; none is the base entry); an unknown or ambiguous build is `provider_build_unknown`, never the base entry; an id in no or two catalogues is `algorithm_unknown` |
| `list_groups()` | each group's `{id, description, exemplars}` |
| `get_group(group, items=10, after=None)` | `{id, members, remaining}`: one page of member ids after `after`, and how many remain |

## Static checks (`validation/catalogue_entry.py`)

An entry's form, every word against the glossary (naming an unlisted term), its engine type against its family's, its id in exactly one catalogue and listed under exactly one family of `catalog/groups.yaml`.

`catalogue_check` runs `entry_check` over every entry. CI no longer checks `measured` labels or coverage: nothing in the repository compares a catalogue value with a run, or checks that every service a build registers has an entry.
