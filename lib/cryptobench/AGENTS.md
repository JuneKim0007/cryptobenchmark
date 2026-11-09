# lib/cryptobench

The implementation guide under `algorithms/` and the Python that reads it, shared by `apps/benchmark-runner` and `apps/perf-repair`. Data never lives here; readers never live in `algorithms/`.

```
../../algorithms/ : data: `<family>_catalogue.yaml` per family, one entry per id `<type>|<canonical>` (key, required, optional, conditions, lifecycle, operations, contract, sourcedOnly, providers, provenance); `common.yaml` sources, keyStrength maps, deterministicRelied; `recipes.yaml` how each parameter object a row names is made; `deviations.yaml` facts shared by a set of names and builds, stated once;
../../algorithms/algorithm-names.yaml : canonical name ← spellings per engine type; key-size suffixes; transformation modes, paddings, per-algorithm synonyms; key formats
../../algorithms/families.yaml : predefined families with fixed descriptions, the one copy
../../algorithms/glossary.yaml : data: one defined meaning per key and value of groups.yaml, the catalogues, recipes.yaml, deviations.yaml, provider-builds.yaml and algorithm-names.yaml, a tree with sections group, algorithm, recipe, plan, deviation, build and names
../../algorithms/groups.yaml : data: per family its exemplars and the listed algorithm ids, from whose catalogue contracts the contract rows come; a person adds ids from group-candidates.yaml
../../algorithms/interchange.yaml : data: per engine type the components that split a group, the rules that read them from a canonical name, what a missing key contract means, and which contract each component states
../../algorithms/provider-builds.yaml : data: every provider build the catalogues' measured facts ran on, keyed <name> @ <build>, with what each says of itself; a behaviour true of a provider and the ids it reaches
../../algorithms/vectors/ : known answers by family
cryptobench/__init__.py : package of the Python library the benchmark runner and perf-repair share
cryptobench/catalogue/__init__.py : package of the implementation guide's readers
cryptobench/catalogue/algorithms.py : reader of the catalogues, checked whole: entry fields, provenance, sources, contracts, type facts, provider overrides; lookup by family and id
cryptobench/catalogue/deviations.py : reads algorithms/deviations.yaml, every word a glossary term; what an entry's providers holds once provider behaviours and deviations apply
cryptobench/catalogue/families.py : the family catalog and (engine type, key kind) → family
cryptobench/catalogue/glossary.py : what_is: a term, a subtree or one value's meaning of glossary.yaml; term_problems: an entry's words checked against it
cryptobench/catalogue/grouping.py : Family, Item (key: what a record names), Profile (isolated: a generator of unknown key contract); key contract values, labels and sources; items.json (schema 1) and profiles.json (schema 5) documents; provider_of, algorithm_of
cryptobench/catalogue/groups.py : reader of groups.yaml, checked whole: one group per family by id, contract rows from each member's catalogue contract, a row at each key contract
cryptobench/catalogue/guide_items.py : guide_items: what the guide says for one effective.yaml's items at this device's builds
cryptobench/catalogue/interchange.py : reader of interchange.yaml: engines, rules by canonical name; a component outside its splits is refused
cryptobench/catalogue/names.py : the names reader: Canonical (name, keySize, known), engine types (what detection scans), fold, same_engine, key formats, name_conflict, key_or_spelling (a conflict keys by its spelling)
cryptobench/catalogue/overrides.py : a provider override's path in an entry, and one build's differences applied to a copy
cryptobench/catalogue/paths.py : DATA: where the guide's data lives
cryptobench/catalogue/provider_builds.py : reads provider-builds.yaml; a build key from what a probe records; a name resolves to one key or is provider_build_unknown
cryptobench/catalogue/recipes.py : reads recipes.yaml, checked whole: one form per recipe, every word and each role's make and lives against the glossary, typed arguments, nested recipes present; the roles a recipe passes
cryptobench/catalogue/reinit.py : whether init runs before every use of an operation, from one build's view of an entry
cryptobench/catalogue/signature.py : Signature and its components, known, convention or unknown; decided, assumed, identity, differing
cryptobench/catalogue/types.py : TypeRow: an algorithm's output kind, Properties, Strength, minSdk and their sources
cryptobench/catalogue/vectors.py : known answers: read and checked whole, filled per provider for one run, --check's coverage lines
cryptobench/catalogue/views.py : what an agent is shown: one entry with only its provider build's overrides (view_for), the groups' ids, descriptions and exemplars (list_groups), one group's members a page at a time (get_group)
cryptobench/coded.py : CODE and code_in, the code word a failure message starts with; InputError, the one coded error a refused input raises (`.code`, `.path`, `.detail`)
cryptobench/document.py : parse_yaml, a YAML text as its one shape (a mapping unless named) or invalid_yaml at its line and column; DocumentKind: a versioned document's accepted schemaVersion (one or several), its reader's refusal text and error type; check, the one schemaVersion check every reader calls
pyproject.toml : the shared library's package metadata
```
