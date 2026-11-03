# Limits

| Limit | Where it shows |
|---|---|
| numbers are device-specific | `measurements.json` `comparability` notes |
| providers seen are those the device registers; a site naming a provider the device lacks, or a name no provider registers, is `not_on_device` with `missing` set, kept and never measured; the next step: add it to `providers.bundled` in global.yaml and rerun the device stage | `sites.json` resolution, `perfrepair.app` and guide lines |
| a project root deeper than 4 levels under the app folder is not found; one with neither settings nor a build file beside a source set is not a root | `perfrepair.app` `not_android_project` |
| app scan reads `.java` and `.kt` source files only; compiled dependencies and `libs/*.jar` are not scanned | `sites.json`, `app.json` `bundled` |
| a constant folds only within its file; a Kotlin import alias of the class is not followed | `sites.json` |
| a name outside `catalog/algorithm-names.yaml` and the probe's aliases keeps its spelling, `known` false; config's reader uses the file alone, not the probe | `sites.json` `canonicalAlgorithm` |
| a probe alias that contradicts the catalog or another provider (e.g. one provider's `RSA/None/OAEPWithSHA-224AndMGF1Padding` → SHA-256) stops the app step that meets it with `name_conflict`; grouping build screens the item `unknown` and asks it | `perfrepair.app`, grouping build |
| a function is found by bracket matching, not a grammar; a call in a field initializer or init block has none | `scopes.json` `unscoped` |
| sinks are pattern matches over the whole function body, not data flow; the key source is too when the lifecycle has no key origin; a field written with `this.`, or a name the function neither declares nor takes (`assignment`, `declaration` in `scope/patterns.yaml`), adds `unknown`; a write through another object (`a.b = x`) or an app wrapper is not seen | `scopes.json` |
| settlement stays in the outermost class of the site's file: a key from another class's call, or a public method's parameter, stays open | `scopes.json`: a requirement with no `settled` |
| the lifecycle follows the object in its method and one method away inside its class only; DI, factories in other classes and callers elsewhere end `partially_bounded`; without the `scope` extra it is `unsupported` | `scopes.json` `lifecycle` |
| default provider resolution, and an app's own provider registration ahead of the device's | `docs/repair.md` limits; options `resolved_by_order` |
| the scope step infers no key or input size, so `harness.yaml` inputs are the run's configured sizes (`from: run`), one size per scope, not the sizes the app passes | `report.json` `inputs` |
| a current and option with no configured size in common get a null input; a function taking bytes, text or a key is then `not_compilable` (`missing_input`) and reported primitive-only | `report.json` `compile` |
| interchangeability is per capture: a `groups.json` belongs to the device folder it was built in, from one manifest | `grouping/groups.json` |
