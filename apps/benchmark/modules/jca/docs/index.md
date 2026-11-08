# jca

```
apps/benchmark/modules/jca/.gitignore : ignores /build
apps/benchmark/modules/jca/README.md : module summary and link to this index
apps/benchmark/modules/jca/build.gradle : Kotlin/JVM 17 library; no project or library dependency
apps/benchmark/modules/jca/docs/index.md : this map
apps/benchmark/modules/jca/src/main/kotlin/failure/Attempt.kt : the one catch rule: Exception or LinkageError as a Result, any other Error thrown
apps/benchmark/modules/jca/src/main/kotlin/failure/ErrorText.kt : a provider's error text: key material removed (URLs kept), capped at 200; refusal of a block as that text or null
apps/benchmark/modules/jca/src/test/kotlin/AttemptTest.kt : the catch rule: which throwables are a result and which escape
```

| rule | value |
|---|---|
| users | discovery (every probe level), preparation (`CasePreparer` steps, interop), benchmark (`CaseCheck`), androidTest (`ScopeCheck`) |
| dependencies | none; module-isolation compiles it alone and puts it on every other module's classpath |
| orchestrator | the per-case boundary that turns any throw into a skip is benchmark's `RunnablePlan`, not this rule |
