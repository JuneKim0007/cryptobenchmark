# module-isolation

Compiles discovery, config, preparation and benchmark each on its own and runs its tests from the module directory.

```
../../apps/benchmark/gradlew -p . test                          # all four
../../apps/benchmark/gradlew -p . :config:test                  # one
../../apps/benchmark/gradlew -p . test -Dexamples.update=true   # rewrite the committed example/ files
```

Sources on each module's classpath: [docs/architecture.md](../../docs/architecture.md).
