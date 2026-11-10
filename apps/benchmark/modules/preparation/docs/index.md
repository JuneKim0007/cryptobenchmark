# preparation

```
apps/benchmark/modules/preparation/.gitignore : ignores /build
apps/benchmark/modules/preparation/README.md : module summary and link to this index
apps/benchmark/modules/preparation/build.gradle : Kotlin/JVM 17 library; snakeyaml 2.3 and api :settings; passes examples.update to tests
apps/benchmark/modules/preparation/docs/index.md : this map
apps/benchmark/modules/preparation/docs/interop.md : cross-provider interop check
apps/benchmark/modules/preparation/docs/operations.md : operation consumption, timed calls, inputs, keys, parameter trees
apps/benchmark/modules/preparation/docs/prepare.md : stages, inputs, selections, resolution, failures
apps/benchmark/modules/preparation/docs/prepared.md : prepared.yaml, skipped.yaml and the case id
apps/benchmark/modules/preparation/example/preparation_capture_example.yaml : example discovery capture input (SUN, SunJCE)
apps/benchmark/modules/preparation/example/preparation_effective_example.yaml : example effective.yaml input
apps/benchmark/modules/preparation/example/preparation_prepared_example.yaml : expected prepared.yaml
apps/benchmark/modules/preparation/example/preparation_skipped_example.yaml : expected skipped.yaml (empty list)
apps/benchmark/modules/preparation/example/preparation_trial_example.yaml : example discovery trial input
apps/benchmark/modules/preparation/src/main/kotlin/Preparation.kt : entry point; prepare(effectiveFile) runs every stage and applies onFailure
apps/benchmark/modules/preparation/src/main/kotlin/adapter/DiscoveryCapability.kt : DeviceCapability over a capture and trial pair
apps/benchmark/modules/preparation/src/main/kotlin/device/CaptureFile.kt : reads capture YAML (schema capture v1) into CapturedDevice
apps/benchmark/modules/preparation/src/main/kotlin/device/ServiceName.kt : uppercase-folded (type, algorithm) lookup key
apps/benchmark/modules/preparation/src/main/kotlin/device/TrialFile.kt : reads trial YAML (schema trial v3) into TrialledDevice
apps/benchmark/modules/preparation/src/main/kotlin/device/dto/ : capture and trial DTOs as preparation reads them
apps/benchmark/modules/preparation/src/main/kotlin/engine/EngineTypeName.kt : uppercase fold for engine type names
apps/benchmark/modules/preparation/src/main/kotlin/engine/EngineTypes.kt : engine type to operations registry, read from engine-operations.yaml, with its TYPE_DEFAULT fallback
apps/benchmark/modules/preparation/src/main/kotlin/global/GlobalReader.kt : reads run and policy sections into GlobalSettings
apps/benchmark/modules/preparation/src/main/kotlin/global/GlobalSettings.kt : validated run-wide settings
apps/benchmark/modules/preparation/src/main/kotlin/global/OnFailure.kt : enum STOP, SKIP
apps/benchmark/modules/preparation/src/main/kotlin/inbound/InboundDocument.kt : effective.yaml split into run, policy, providers sections
apps/benchmark/modules/preparation/src/main/kotlin/inbound/InboundFile.kt : reads effective.yaml (schema config v1)
apps/benchmark/modules/preparation/src/main/kotlin/input/CipherKeys.kt : picks the encrypt or decrypt key from KeyMaterial
apps/benchmark/modules/preparation/src/main/kotlin/input/InputBytes.kt : seeded input bytes (java.util.Random(seed))
apps/benchmark/modules/preparation/src/main/kotlin/input/OperationInput.kt : sealed case input: None, Message, Ciphertext, SignedMessage
apps/benchmark/modules/preparation/src/main/kotlin/interop/ : cross-provider interop check: plan file, checks, verdicts, the plan run, interop.yaml
apps/benchmark/modules/preparation/src/main/kotlin/key/generate/KeyInitializer.kt : KeyGenerator and KeyPairGenerator init
apps/benchmark/modules/preparation/src/main/kotlin/key/generate/KeyMaterial.kt : sealed key material: None, Secret, Pairs
apps/benchmark/modules/preparation/src/main/kotlin/key/generate/KeyMaterialGenerator.kt : builds KeyMaterial from a KeyRecipe
apps/benchmark/modules/preparation/src/main/kotlin/key/plan/KeyCandidate.kt : candidate key algorithm and optional size
apps/benchmark/modules/preparation/src/main/kotlin/key/plan/KeyPlanner.kt : chooses the KeyRecipe for a case
apps/benchmark/modules/preparation/src/main/kotlin/key/plan/KeyRecipe.kt : sealed recipe: None, Secret, Pair, Unavailable
apps/benchmark/modules/preparation/src/main/kotlin/measurement/BenchmarkCase.kt : one case's axes, validated
apps/benchmark/modules/preparation/src/main/kotlin/measurement/CaseName.kt : builds the case id
apps/benchmark/modules/preparation/src/main/kotlin/measurement/Operation.kt : enum of the ten operations
apps/benchmark/modules/preparation/src/main/kotlin/measurement/Phase.kt : enum WARM
apps/benchmark/modules/preparation/src/main/kotlin/measurement/Variant.kt : enum fixed, notFixed
apps/benchmark/modules/preparation/src/main/kotlin/operation/AgreeKeyDefinition.kt : AGREE_KEY definition
apps/benchmark/modules/preparation/src/main/kotlin/operation/CallTrace.kt : the engine an EngineCall holds and its init count, read outside the timed call by the end-to-end check
apps/benchmark/modules/preparation/src/main/kotlin/operation/CaseArguments.kt : spec pool, seeded message, key accessors for definitions
apps/benchmark/modules/preparation/src/main/kotlin/operation/CipherCall.kt : one timed doFinal into a preallocated buffer, init and getInstance by perCall; refuses parameters a provider will not repeat
apps/benchmark/modules/preparation/src/main/kotlin/operation/ComputeMacDefinition.kt : COMPUTE_MAC definition
apps/benchmark/modules/preparation/src/main/kotlin/operation/DecryptDefinition.kt : DECRYPT definition; builds ciphertext input
apps/benchmark/modules/preparation/src/main/kotlin/operation/DigestDefinition.kt : DIGEST definition
apps/benchmark/modules/preparation/src/main/kotlin/operation/EncryptDefinition.kt : ENCRYPT definition
apps/benchmark/modules/preparation/src/main/kotlin/operation/EngineCall.kt : one timed call over a JCA engine: what it redoes per call, by PerCall; its replay with the last drawn parameters; its CallTrace
apps/benchmark/modules/preparation/src/main/kotlin/operation/EngineInit.kt : an engine's init told its call index, the index unboxed
apps/benchmark/modules/preparation/src/main/kotlin/operation/GenerateKeyDefinition.kt : GENERATE_KEY definition
apps/benchmark/modules/preparation/src/main/kotlin/operation/GenerateKeyPairDefinition.kt : GENERATE_KEY_PAIR definition
apps/benchmark/modules/preparation/src/main/kotlin/operation/Invocation.kt : the timed call (perIteration), once(), again() (the last call replayed with its parameters), the engine it calls and its CallTrace
apps/benchmark/modules/preparation/src/main/kotlin/operation/Invocations.kt : of(prepared) to the case's Invocation
apps/benchmark/modules/preparation/src/main/kotlin/operation/KeyShape.kt : enum NONE, SECRET, PAIR, PEER_PAIRS, DEVICE_DECIDES
apps/benchmark/modules/preparation/src/main/kotlin/operation/OperationDefinition.kt : interface: what an operation consumes and its call
apps/benchmark/modules/preparation/src/main/kotlin/operation/OperationDefinitions.kt : Operation to definition map
apps/benchmark/modules/preparation/src/main/kotlin/operation/PerCall.kt : enum of what one timed call does: operation, initAndOperation, getInstanceInitAndOperation
apps/benchmark/modules/preparation/src/main/kotlin/operation/SetupCatalog.kt : reads setup-catalog.yaml: a case's variants and its PerCall
apps/benchmark/modules/preparation/src/main/kotlin/operation/SignDefinition.kt : SIGN definition
apps/benchmark/modules/preparation/src/main/kotlin/operation/TypeDefaultDefinition.kt : TYPE_DEFAULT definition (no-op call)
apps/benchmark/modules/preparation/src/main/kotlin/operation/VerifyDefinition.kt : VERIFY definition; builds signed-message input
apps/benchmark/modules/preparation/src/main/kotlin/parameter/bind/BindException.kt : bind_failed: <path>: <detail>
apps/benchmark/modules/preparation/src/main/kotlin/parameter/bind/BindPolicy.kt : classes a parameter tree may name
apps/benchmark/modules/preparation/src/main/kotlin/parameter/bind/BoundParameters.kt : compiled tree; varies, next(); cycling(specs) for the end-to-end check's fixed values
apps/benchmark/modules/preparation/src/main/kotlin/parameter/bind/ParameterBinder.kt : compiles a parameter tree into a ValueNode
apps/benchmark/modules/preparation/src/main/kotlin/parameter/bind/ValueCoercion.kt : YAML value to constructor parameter type
apps/benchmark/modules/preparation/src/main/kotlin/parameter/bind/ValueNode.kt : tree nodes: Literal, Fresh, Cycle, StaticField, Construction
apps/benchmark/modules/preparation/src/main/kotlin/parameter/resolve/Fingerprint.kt : first 8 hex chars of SHA-256
apps/benchmark/modules/preparation/src/main/kotlin/parameter/resolve/KeyFields.kt : keyBits and curve of a key, by key interface
apps/benchmark/modules/preparation/src/main/kotlin/parameter/resolve/PerInitValue.kt : whether an IvParameterSpec value is an IV or a constant the provider fills in
apps/benchmark/modules/preparation/src/main/kotlin/parameter/resolve/ResolvedParameters.kt : what the provider used after one call; key names
apps/benchmark/modules/preparation/src/main/kotlin/parameter/resolve/SpecFields.kt : fields of reported parameters, by spec class
apps/benchmark/modules/preparation/src/main/kotlin/port/Availability.kt : Available or Unavailable(reason)
apps/benchmark/modules/preparation/src/main/kotlin/port/DeviceCapability.kt : device port: providers, check, measuredKeyAlgorithm
apps/benchmark/modules/preparation/src/main/kotlin/prepare/CasePreparer.kt : one case: key, bind, input, one call, parameter read-back; a failed step throws PreparationException with its code
apps/benchmark/modules/preparation/src/main/kotlin/prepare/ChartGroup.kt : which cases a chart may compare, from the service type, then the key kind
apps/benchmark/modules/preparation/src/main/kotlin/prepare/Listing.kt : the cases and rejected selections of an effective file, with its run settings; no provider called
apps/benchmark/modules/preparation/src/main/kotlin/prepare/PreparationException.kt : one step of a case's preparation failed: its code and the scrubbed failure
apps/benchmark/modules/preparation/src/main/kotlin/prepare/PreparedCase.kt : a built case: case, recipe, key, parameters, keyParameters, input, resolvedParameters; its chart group
apps/benchmark/modules/preparation/src/main/kotlin/prepare/StoppedOnFailureException.kt : thrown under onFailure stop
apps/benchmark/modules/preparation/src/main/kotlin/record/PreparedDocument.kt : prepared.yaml document shape
apps/benchmark/modules/preparation/src/main/kotlin/record/PreparedFile.kt : prepared.yaml: the listed cases, then each one's prepared entry, or removed when it failed
apps/benchmark/modules/preparation/src/main/kotlin/report/Skip.kt : one skipped item (stage, provider, type, name, reason)
apps/benchmark/modules/preparation/src/main/kotlin/report/SkipFile.kt : skipped.yaml: written whole, read back, one skip added
apps/benchmark/modules/preparation/src/main/kotlin/request/BenchmarkRequest.kt : selections and global settings, validated
apps/benchmark/modules/preparation/src/main/kotlin/request/PrimitiveReader.kt : providers section to selections
apps/benchmark/modules/preparation/src/main/kotlin/request/Selection.kt : one requested primitive entry, validated
apps/benchmark/modules/preparation/src/main/kotlin/resolve/CaseResolver.kt : selections to cases and rejections
apps/benchmark/modules/preparation/src/main/kotlin/resolve/Rejection.kt : one rejected selection or provider with reason
apps/benchmark/modules/preparation/src/main/kotlin/resolve/Resolution.kt : cases and rejections result
apps/benchmark/modules/preparation/src/main/kotlin/resolve/SelectionCheck.kt : per-selection rejection rules
apps/benchmark/modules/preparation/src/main/kotlin/resolve/SelectionExpander.kt : cartesian expansion of a selection into cases
apps/benchmark/modules/preparation/src/main/kotlin/shared/DocumentFields.kt : typed field reads with named errors
apps/benchmark/modules/preparation/src/main/kotlin/shared/DocumentFile.kt : YAML file read (schemaVersion check) and write
apps/benchmark/modules/preparation/src/main/kotlin/shared/FailureText.kt : a failure as one record line: scrubbed and capped, object identity hashes dropped
apps/benchmark/modules/preparation/src/main/kotlin/shared/YamlCodec.kt : SnakeYAML setup: safe load, no duplicate keys, indent 2
apps/benchmark/modules/preparation/src/main/resources/io/github/junekim0007/cryptobench/preparation/engine/engine-operations.yaml : per engine type the operations the harness times, and the fallback; apps/benchmark-runner/results/manifest.py copies the types into each run's manifest.yaml `operations`
apps/benchmark/modules/preparation/src/main/resources/io/github/junekim0007/cryptobench/preparation/operation/setup-catalog.yaml : per engine type, cipher mode or Mac name suffix, what a fixed call still does; JCA contract per row
apps/benchmark/modules/preparation/src/test/kotlin/BenchmarkCaseTest.kt : case id and case validation tests
apps/benchmark/modules/preparation/src/test/kotlin/BenchmarkRequestTest.kt : request shape-error tests
apps/benchmark/modules/preparation/src/test/kotlin/BoundParametersTest.kt : cycling fixed specs in turn
apps/benchmark/modules/preparation/src/test/kotlin/CaseResolverTest.kt : expansion and rejection tests
apps/benchmark/modules/preparation/src/test/kotlin/ChartGroupTest.kt : chart group tests
apps/benchmark/modules/preparation/src/test/kotlin/CipherCallTest.kt : CipherCall per-call init, instance and refusal tests
apps/benchmark/modules/preparation/src/test/kotlin/DiscoveryCapabilityTest.kt : capture and trial availability tests
apps/benchmark/modules/preparation/src/test/kotlin/EffectiveFixture.kt : effective.yaml test fixture builder
apps/benchmark/modules/preparation/src/test/kotlin/EngineCallTest.kt : what each PerCall makes, inits and operates per call; the trace's engine and inits; again() with the last call's parameters; no check-only state in the timed call
apps/benchmark/modules/preparation/src/test/kotlin/EngineTypesTest.kt : engine type registry tests
apps/benchmark/modules/preparation/src/test/kotlin/ExampleFilesTest.kt : prepares example/ and compares the committed outputs
apps/benchmark/modules/preparation/src/test/kotlin/FailureTextTest.kt : a provider's failure as preparation writes it: key encodings removed, identity hash dropped, within the cap
apps/benchmark/modules/preparation/src/test/kotlin/GlobalReaderTest.kt : run and policy read tests
apps/benchmark/modules/preparation/src/test/kotlin/InboundFileTest.kt : effective.yaml section and schema tests
apps/benchmark/modules/preparation/src/test/kotlin/InteropOracleTest.kt : interop verdict and plan-file tests
apps/benchmark/modules/preparation/src/test/kotlin/InvocationTest.kt : invocation repeatability, IV reuse, both variants, fresh IV under fixed
apps/benchmark/modules/preparation/src/test/kotlin/KeyMaterialGeneratorTest.kt : key generation tests
apps/benchmark/modules/preparation/src/test/kotlin/KeyPlannerTest.kt : key recipe planning tests
apps/benchmark/modules/preparation/src/test/kotlin/OperationContractTest.kt : per-operation consumption contract tests
apps/benchmark/modules/preparation/src/test/kotlin/OperationInputTest.kt : per-operation input tests
apps/benchmark/modules/preparation/src/test/kotlin/ParameterBinderTest.kt : parameter tree binding tests
apps/benchmark/modules/preparation/src/test/kotlin/ParityFixturesTest.kt : parity/ guide and effective read to their .json values and accepted by Guide and InboundFile; today's duplicate-key refusal
apps/benchmark/modules/preparation/src/test/kotlin/PreparationFixture.kt : shared preparation test fixtures
apps/benchmark/modules/preparation/src/test/kotlin/PreparationPolicyTest.kt : onFailure policy tests
apps/benchmark/modules/preparation/src/test/kotlin/PreparedCaseTest.kt : prepared-case tests
apps/benchmark/modules/preparation/src/test/kotlin/PreparedFileTest.kt : prepared.yaml content tests
apps/benchmark/modules/preparation/src/test/kotlin/PrimitiveReaderTest.kt : providers-section read tests
apps/benchmark/modules/preparation/src/test/kotlin/ResolvedParametersTest.kt : read-back tests per parameter kind: GCM, CBC, key wrap, OAEP, PSS, EC curve, key size
apps/benchmark/modules/preparation/src/test/kotlin/SetupCatalogTest.kt : catalog rows per engine type and mode, variants per type
```
