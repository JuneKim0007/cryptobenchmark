# module-isolation

Compiles each module on its own — only snakeyaml, JUnit and the shared `settings` key table on the classpath, no other project dependency —
and runs its tests from the module directory, so `example/` resolves.

`benchmark` is the one exception: it compiles with `preparation`, because it times the invocation
preparation builds. It still compiles without `config` and without `discovery`.

A module that reaches into another module's Kotlin stops compiling here. That is the check.

```
../jca-contract/gradlew -p . test            # all four
../jca-contract/gradlew -p . :config:test    # one
```

Regenerate the committed examples after a schema change:

```
../jca-contract/gradlew -p . test -Dexamples.update=true
```
