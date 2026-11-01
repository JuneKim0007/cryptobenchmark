# Repair

Command: `python3 -m perfrepair.repair <step> --run <run> --app <app>`; every step reads and writes under `<run>/apps/<app>/`.

| Step | Flags | Input | Output |
|---|---|---|---|
| dossier | `--source <app root>` | `scopes.json`, `app.json`, `grouping/groups.json`, `rows.json`, `measurements.json` | `dossiers.json`, validated before writing |
| test-set | `-o` | `dossiers.json` | YAML test set at `-o`: each scope's current item and every option, once each |
| edit | `--source <app root>` | `scopes.json`, `replacements.json`, the app tree (read only) | `edits.json`; `original/` and `patched/` copies of the changed files |
| harness | none | `scopes.json`, `replacements.json`, `edits.json`, `original/`, `patched/` | `harness.yaml`; `harness/<scope>/before.<ext>`, `after.<ext>` |

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

## harness.yaml

```yaml
schemaVersion: 1
app: <name>
scopes:
  - id: <scope id>
    language: java|kotlin
    function: <signature>
    before: harness/<scope id>/before.java
    after: harness/<scope id>/after.java
    imports: [<the file's import lines>]
    inputs: {inputSize: <bytes or null>, keySize: <bits or null>}
    option: <item id>
    metrics: [timeNs, allocationCount, energyUj]
    dependencies: [<identifiers used but not defined in the function>]
```

- Paths are relative to the folder of `harness.yaml`; only applied scopes are listed.
- `before` and `after` are lines `scope.start..scope.end` of the original and patched file, verbatim.
- `dependencies` is the union over both functions: identifiers not declared in the function, not after another receiver's `.`, not a keyword, not imported, and not in `repair/names.yaml`.

## Limits

| Limit | Rule |
|---|---|
| dependencies | token rules only: Kotlin `when` branch labels and infix operands read as declared; wildcard imports hide nothing |
| argument split | generic angle brackets are not counted, so `f(Map<A, B>)` reads as two arguments |
| pin with an app-supplied IV | rejected; the IV length cannot be changed without changing the app's data flow |
| default provider | the first by precedence that registers the name |
| provider rejecting the key at `init` | not skipped |
| Cipher transformation served only through its base service | not resolved |
