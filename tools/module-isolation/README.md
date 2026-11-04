# module-isolation

Compiles discovery, config, preparation and benchmark each on its own and runs its tests from the module directory.

```
../../gradlew -p . test                          # all four
../../gradlew -p . :config:test                  # one
../../gradlew -p . test -Dexamples.update=true   # rewrite the committed example/ files
```

Sources on each module's classpath: [docs/architecture.md](../../docs/architecture.md).
