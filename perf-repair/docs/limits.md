# Limits

| Limit | Where it shows |
|---|---|
| numbers are device-specific | `measurements.json` `comparability` notes |
| providers seen are those the device registers; a provider bundled in an app is `provider_not_on_device` | `sites.json` resolution |
| a project root deeper than 4 levels under the app folder is not found; one with neither settings nor a build file beside a source set is not a root | `perfrepair.app` `not_android_project` |
| app scan reads `.java` and `.kt` source files only; compiled dependencies and `libs/*.jar` are not scanned | `sites.json`, `app.json` `bundled` |
| a constant folds only within its file; a Kotlin import alias of the class is not followed | `sites.json` |
| a name outside `catalog/algorithm-names.yaml` and the probe's aliases keeps its spelling, `known` false; config's reader uses the file alone, not the probe | `sites.json` `canonicalAlgorithm` |
| a probe alias that contradicts the catalog or another provider (e.g. one provider's `RSA/None/OAEPWithSHA-224AndMGF1Padding` → SHA-256) stops the command that meets it with `name_conflict` | `perfrepair.app`, grouping build |
| a function is found by bracket matching, not a grammar; a call in a field initializer or init block has none | `scopes.json` `unscoped` |
| sinks and key source are pattern matches over the whole function body, not data flow | `scopes.json` |
| default provider resolution | `docs/repair.md` limits |
| the scope step infers no key or input size, so `harness.yaml` inputs are the run's configured sizes (`from: run`), one size per scope, not the sizes the app passes | `report.json` `inputs` |
| a current and option with no configured size in common get a null input; a function taking bytes, text or a key is then `not_compilable` (`missing_input`) and reported primitive-only | `report.json` `compile` |
| interchangeability is per capture: a `groups.json` belongs to the run directory built from one manifest | `grouping/groups.json` |
