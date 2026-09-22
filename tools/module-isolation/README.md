# module-isolation

Compiles each module on its own — only snakeyaml and JUnit on the classpath, no project dependency —
and runs its tests from the module directory, so `example/` resolves.

A module that reaches into another module's Kotlin stops compiling here. That is the check.

```
../jca-contract/gradlew -p . test            # all three
../jca-contract/gradlew -p . :config:test    # one
```

Regenerate the committed examples after a schema change:

```
../jca-contract/gradlew -p . test -Dexamples.update=true
```
