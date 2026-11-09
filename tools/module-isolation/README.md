# module-isolation

Compiles files, jca, discovery, config, preparation and benchmark each on its own and runs its tests from the module directory.
`architecture` checks their classes against `layers.yaml`; `handoff_check.py` checks androidTest and cli sources ([rules](../../docs/contributing/code.md#dependency-rules)).

```
../../apps/benchmark/gradlew -p . test                          # all four and architecture
../../apps/benchmark/gradlew -p . :config:test                  # one
../../apps/benchmark/gradlew -p . test -Dexamples.update=true   # rewrite the committed example/ files
```

Sources on each module's classpath: [docs/architecture.md](../../docs/architecture.md).
