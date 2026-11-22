# jca

```
apps/benchmark/modules/jca/README.md : module summary and link to this index
apps/benchmark/modules/jca/build.gradle : Kotlin/JVM 17 library; no project or library dependency
apps/benchmark/modules/jca/docs/index.md : this map
apps/benchmark/modules/jca/src/main/kotlin/bind/BindException.kt : bind_failed: <path>: <detail>
apps/benchmark/modules/jca/src/main/kotlin/bind/BindPolicy.kt : classes a parameter tree may name
apps/benchmark/modules/jca/src/main/kotlin/bind/BoundParameters.kt : compiled tree; varies, next(); cycling(specs) for the end-to-end check's fixed values
apps/benchmark/modules/jca/src/main/kotlin/bind/ParameterBinder.kt : compiles a parameter tree into a ValueNode; preparation and benchmark
apps/benchmark/modules/jca/src/main/kotlin/bind/ValueCoercion.kt : YAML value to constructor parameter type
apps/benchmark/modules/jca/src/main/kotlin/bind/ValueNode.kt : tree nodes: Literal, Fresh, Cycle, StaticField, Construction
apps/benchmark/modules/jca/src/main/kotlin/failure/Attempt.kt : the one catch rule: Exception or LinkageError as a Result, any other Error thrown
apps/benchmark/modules/jca/src/main/kotlin/failure/ErrorText.kt : a provider's error text: key material removed (URLs kept), capped at 200; refusal of a block as that text or null
apps/benchmark/modules/jca/src/main/kotlin/peer/PeerPair.kt : an agreement's second pair on the first one's EC curve, DH group or XEC named curve (initialized only when the default differs or refuses); discovery and preparation
apps/benchmark/modules/jca/src/main/kotlin/reflect/Reflect.kt : invoke: a reflective call that throws what the method threw, never InvocationTargetException
apps/benchmark/modules/jca/src/test/kotlin/AttemptTest.kt : the catch rule: which throwables are a result and which escape
apps/benchmark/modules/jca/src/test/kotlin/PeerPairTest.kt : DH by key size, EC, X25519 and X448 peers share their domain and agree
apps/benchmark/modules/jca/src/test/kotlin/ReflectTest.kt : invoke returns the method's value and throws its own exception
```

| rule | value |
|---|---|
| users | discovery (every probe level), preparation (`CasePreparer` steps, interop), benchmark (`CaseCheck`), androidTest (`ScopeCheck`); `Reflect`: preparation's keystore spec and key info, discovery's cipher facts; `PeerPair`: discovery's agreement trials, preparation's second key pair (interop included) |
| dependencies | none (JDK only); module-isolation compiles it alone and puts it on every other module's classpath |
| orchestrator | the per-case boundary that turns any throw into a skip is benchmark's `RunnablePlan`, not this rule |
