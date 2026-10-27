# Limits

| Limit | Where it shows |
|---|---|
| numbers are device-specific | `measurements.json` `comparability` notes |
| providers seen are those the device registers; a provider bundled in an app is `provider_not_on_device` | `sites.json` resolution |
| app scan reads `.java` and `.kt` source files only; compiled dependencies and `libs/*.jar` are not scanned | `sites.json`, `app.json` `bundled` |
| a constant folds only within its file; a Kotlin import alias of the class is not followed | `sites.json` |
| a function is found by bracket matching, not a grammar; a call in a field initializer or init block has none | `scopes.json` `unscoped` |
| sinks and key source are pattern matches over the whole function body, not data flow | `scopes.json` |
| default provider resolution | `docs/repair.md` limits |
| interchangeability is per capture: a `groups.json` belongs to the run directory built from one manifest | `grouping/groups.json` |
