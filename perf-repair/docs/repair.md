# Repair

Command: `python3 -m perfrepair.repair <step> --device-results <device> --app <src>`; every step reads and writes under `<device>/<app>/`; `<src>` is only read and gives `<app>` (`docs/artifacts.md`).

| Step | Flags | Input | Output |
|---|---|---|---|
| dossier | | `scopes.json`, `units.json`, `app.json`, `grouping/groups.json`, `rows.json`, `measurements.json` | `dossiers.json`, validated before writing |
| test-set | `-o` | `dossiers.json` | YAML test set at `-o`: each scope's current item and every option, once each |
| edit | | `scopes.json`, `replacements.json`, the app tree (read only) | `edits.json`; `original/` and `patched/` copies of the changed files |
| harness | | `scopes.json`, `replacements.json`, `edits.json`, `dossiers.json`, `original/`, `patched/`, the manifest's `effective.yaml` | `harness.yaml`; `harness/<scope>/before.<ext>`, `after.<ext>` |

- test-set refuses a `dossiers.json` of another app, and one with no scope that has an option.
- A per-app benchmark run on the test set measures only what the app uses and its swap candidates.

## Edit kinds

| Kind | Fields | Change |
|---|---|---|
| `set_provider` | `provider` | a string provider argument or the literal inside `getProvider("X")` replaced; appended when the call has one argument |
| `set_algorithm` | `algorithm` | the literal first argument replaced |
| `pin_parameters` | `parameters`: spec fields | the spec in `repair/edit/specs.yaml` whose fields cover the keys, appended to the one `init` on the engine; an existing spec of that class keeps its unpinned arguments |

- A scope's call is re-found on `scope.line`, inside lines `scope.start..scope.end`, by its text with whitespace and comments ignored.
- `scope.call` is the call's source from the engine type to its closing parenthesis.
- The `init` is `v.init(` where `v` is assigned the call's result, or a bare `init(` in a Kotlin `.apply { }` or `.run { }` on the call.
- A random-bytes field (`ivBytes`) renders a fresh `SecureRandom` array, only for an `init` whose mode is in `encryptingModes`.
- Splices keep line numbers: newlines of a replaced span follow the new text.
- Every applied scope of one file shares that file's `patched/` copy.

## edits.json

`{"schemaVersion": 1, "app", "edits": [{"scope", "status": "applied"|"rejected", "reason", "diff"}]}`, one row per `replace` decision, in scope id order; `reason` is null when applied, `diff` empty when rejected.

| Reason | Means |
|---|---|
| `call_moved` | the call text is not on `scope.line`, or the line range is outside the file |
| `ambiguous_call` | the call text occurs twice on that line |
| `function_span` | braces in lines `start..end` do not balance |
| `unbalanced_call` | an argument list or block does not close |
| `unsupported_expression` | an argument is neither a literal nor `getProvider("X")`, the init's spec argument is not the table's spec, or a random field cannot be rendered |
| `algorithm_not_literal` | `set_algorithm` on a call whose algorithm is not a string literal |
| `no_init`, `ambiguous_init` | zero or several `init` calls on the engine in the function |
| `missing_parameter`, `unknown_parameters` | an edit lacks its field, or its fields match no single spec |
| `unsupported_kind`, `unsupported_language` | an edit kind or file suffix this step does not handle |
| `file_missing`, `no_edits`, `no_change`, `overlapping_edits` | the source file is gone, the replacement has no edits, the edits change nothing, two scopes' spans overlap |
| `unit_member_rejected` | another member of its unit was rejected, so no member is applied; the row's `blockedBy` is `<scope>: <reason>`; the report's edit reason carries it |

## harness.yaml

```yaml
schemaVersion: 4
app: <name>
scopes:
  - id: <scope id>
    language: java|kotlin
    function: <the scope's function name>
    before: harness/<scope id>/before.java
    after: harness/<scope id>/after.java
    imports: [<the file's import lines the functions use>]
    inputs: {inputSize: <bytes or null>, keySize: <bits or null>, from: app|run}
    current: <the dossier's current item>
    option: <the chosen item>
    metrics: [timeNs, allocationCount, energyJ]
    dependencies: [<identifiers used but not defined in the function>]
    notMeasurable: null|no_operation
    inverse: null|{partner: <scope id>, role: produce|consume}
```

- Paths are relative to the folder of `harness.yaml`; only applied scopes are listed.
- `inverse` is the scope's partner by an `inverse` link of `units.json`, both sides applied; cryptobenchmark's round trip takes it, never a name.
- `current` and `option` are two different items: the pair cryptobenchmark's primitive interop oracle checks.
- `metrics` names `benchmark.json` keys; energy is `energyJ`, joules per operation.
- `before` and `after` are lines `scope.start..scope.end` of the original and patched file, verbatim. When two units applied edits in one function, `after` comes from `patched-alone/<unit>/`, that unit's edits only: the function is measured as original, A swapped only, B swapped only, never with both, so no change is counted twice.
- `imports` keeps a line whose simple name or alias a function's text uses (Kotlin: in any position, since an extension reads as a member; an operator or delegate convention name always); a header annotation's import is dropped with the annotation; a wildcard stays only while a dependency is unresolved.
- `notMeasurable: no_operation`: the function only creates, configures or hands back its primitive (`repair/operation.py`, setup names in `repair/setup_calls.yaml`); cryptobenchmark records it and never generates it, so no number describes a factory. A form the check cannot read counts as an operation.
- `dependencies` is the union over both functions: identifiers not declared in the function, not after another receiver's `.`, not a keyword, not imported, and not in `repair/names.yaml`.
- `inputs` is one entry per scope, never one per size; `from` says where its sizes came from:

| `inputs` | rule |
|---|---|
| `from: app` | the scope's `inputSize` or `keySize` is set: both are taken from the scope as they are; the run is not read |
| `from: run` | otherwise; an item's sizes are the union over its `providers.<p>.<type>.<name>` and `<name>@<group>` entries of `effective.yaml`, the name matched case-insensitively |
| item `inputSize`s | the entry's `inputSizes`, else `run.inputSizes` (preparation's rule) |
| item `keySize`s | the entry's `keySizes`; none when the provider chose the size (`providerDefaults: [keySize]` records no value) |
| chosen size | the largest size configured for both `current` and `option`, so before and after run at a size the benchmark measured for each, and the largest because it spreads the function's per-call setup over the most data; none shared is null, which the harness reports `missing_input` |
| `item_not_configured` | `current` or `option` has no entry: the device folder's manifest is not the run the groups came from; the step fails |
| `missing_effective` | the manifest has no `files.effective`; the step fails |

## Limits

| Limit | Rule |
|---|---|
| dependencies | token rules only: Kotlin `when` branch labels and infix operands read as declared; wildcard imports hide nothing |
| imports | by name only: a Java name used only as a member after `.` keeps no import; a kept wildcard may resolve none of the names |
| no_operation | tokens around the call, not data flow: a field the function sets is an operation when it calls one of its own methods |
| argument split | generic angle brackets are not counted, so `f(Map<A, B>)` reads as two arguments |
| pin with an app-supplied IV | rejected; the IV length cannot be changed without changing the app's data flow |
| default provider | the first by precedence that registers the name; a Cipher transformation also matches like JCA: `A/M`, `A//P`, then `A`, within the service's `SupportedModes` and `SupportedPaddings` |
| provider rejecting the key at `init` | not skipped |
| Cipher transformation served only through its base service | not resolved |
