# preparation

```
modules/preparation/.gitignore : ignores /build
modules/preparation/README.md : module summary and link to this index
modules/preparation/build.gradle : Kotlin/JVM 17 library; snakeyaml 2.3 and api :settings; passes examples.update and trial to tests
modules/preparation/docs/index.md : this map
modules/preparation/docs/interop.md : cross-provider interop check
modules/preparation/docs/operations.md : operation consumption, timed calls, inputs, keys, parameter trees
modules/preparation/docs/prepare.md : stages, inputs, selections, resolution, failures
modules/preparation/docs/prepared.md : prepared.yaml, skipped.yaml and the case id
modules/preparation/example/preparation_capture_example.yaml : example discovery capture input (SUN, SunJCE)
modules/preparation/example/preparation_effective_example.yaml : example effective.yaml input
modules/preparation/example/preparation_prepared_example.yaml : expected prepared.yaml
modules/preparation/example/preparation_skipped_example.yaml : expected skipped.yaml (empty list)
modules/preparation/example/preparation_trial_example.yaml : example discovery trial input
modules/preparation/src/main/kotlin/Preparation.kt : entry point; prepare(effectiveFile) runs every stage and applies onFailure
modules/preparation/src/main/kotlin/adapter/DiscoveryCapability.kt : DeviceCapability over a capture and trial pair
modules/preparation/src/main/kotlin/device/CaptureFile.kt : reads capture YAML (schema capture v1) into CapturedDevice
modules/preparation/src/main/kotlin/device/ServiceName.kt : uppercase-folded (type, algorithm) lookup key
modules/preparation/src/main/kotlin/device/TrialFile.kt : reads trial YAML (schema trial v2) into TrialledDevice
modules/preparation/src/main/kotlin/device/dto/ : capture and trial DTOs as preparation reads them
modules/preparation/src/main/kotlin/engine/EngineTypes.kt : engine type to operations registry with TYPE_DEFAULT fallback
modules/preparation/src/main/kotlin/global/GlobalReader.kt : reads run and policy sections into GlobalSettings
modules/preparation/src/main/kotlin/global/GlobalSettings.kt : validated run-wide settings
modules/preparation/src/main/kotlin/global/OnFailure.kt : enum STOP, SKIP
modules/preparation/src/main/kotlin/inbound/InboundDocument.kt : effective.yaml split into run, policy, providers sections
modules/preparation/src/main/kotlin/inbound/InboundFile.kt : reads effective.yaml (schema config v1)
modules/preparation/src/main/kotlin/input/CipherKeys.kt : picks the encrypt or decrypt key from KeyMaterial
modules/preparation/src/main/kotlin/input/InputBytes.kt : seeded input bytes (java.util.Random(seed))
modules/preparation/src/main/kotlin/input/OperationInput.kt : sealed case input: None, Message, Ciphertext, SignedMessage
modules/preparation/src/main/kotlin/interop/ : cross-provider interop check: plan file, checks, verdicts, the plan run, interop.yaml
modules/preparation/src/main/kotlin/key/generate/DefaultKeyInitializer.kt : default KeyGenerator and KeyPairGenerator init
modules/preparation/src/main/kotlin/key/generate/KeyInitializer.kt : per-provider key-init port
modules/preparation/src/main/kotlin/key/generate/KeyMaterial.kt : sealed key material: None, Secret, Pairs
modules/preparation/src/main/kotlin/key/generate/KeyMaterialGenerator.kt : builds KeyMaterial from a KeyRecipe
modules/preparation/src/main/kotlin/key/plan/KeyAlgorithmName.kt : key-algorithm candidates from type and algorithm name
modules/preparation/src/main/kotlin/key/plan/KeyCandidate.kt : candidate key algorithm and optional size
modules/preparation/src/main/kotlin/key/plan/KeyPlanner.kt : chooses the KeyRecipe for a case
modules/preparation/src/main/kotlin/key/plan/KeyRecipe.kt : sealed recipe: None, Secret, Pair, Unavailable
modules/preparation/src/main/kotlin/measurement/BenchmarkCase.kt : one case's axes, validated
modules/preparation/src/main/kotlin/measurement/CaseName.kt : builds the case id
modules/preparation/src/main/kotlin/measurement/EngineTypeName.kt : uppercase fold for engine type names
modules/preparation/src/main/kotlin/measurement/Operation.kt : enum of the ten operations
modules/preparation/src/main/kotlin/measurement/Phase.kt : enum WARM, COLD
modules/preparation/src/main/kotlin/operation/AgreeKeyDefinition.kt : AGREE_KEY definition
modules/preparation/src/main/kotlin/operation/CaseArguments.kt : spec pool, seeded message, key accessors for definitions
modules/preparation/src/main/kotlin/operation/CipherCall.kt : one timed doFinal into a preallocated buffer; decides re-init
modules/preparation/src/main/kotlin/operation/ComputeMacDefinition.kt : COMPUTE_MAC definition
modules/preparation/src/main/kotlin/operation/DecryptDefinition.kt : DECRYPT definition; builds ciphertext input
modules/preparation/src/main/kotlin/operation/DigestDefinition.kt : DIGEST definition
modules/preparation/src/main/kotlin/operation/EncryptDefinition.kt : ENCRYPT definition
modules/preparation/src/main/kotlin/operation/GenerateKeyDefinition.kt : GENERATE_KEY definition
modules/preparation/src/main/kotlin/operation/GenerateKeyPairDefinition.kt : GENERATE_KEY_PAIR definition
modules/preparation/src/main/kotlin/operation/Invocation.kt : the timed call (perIteration), once() and the engine it calls
modules/preparation/src/main/kotlin/operation/Invocations.kt : of(prepared) to the case's Invocation
modules/preparation/src/main/kotlin/operation/KeyShape.kt : enum NONE, SECRET, PAIR, PEER_PAIRS, DEVICE_DECIDES
modules/preparation/src/main/kotlin/operation/OperationDefinition.kt : interface: what an operation consumes and its call
modules/preparation/src/main/kotlin/operation/OperationDefinitions.kt : Operation to definition map
modules/preparation/src/main/kotlin/operation/SignDefinition.kt : SIGN definition
modules/preparation/src/main/kotlin/operation/TypeDefaultDefinition.kt : TYPE_DEFAULT definition (no-op call)
modules/preparation/src/main/kotlin/operation/VerifyDefinition.kt : VERIFY definition; builds signed-message input
modules/preparation/src/main/kotlin/parameter/bind/BindException.kt : bind_failed: <path>: <detail>
modules/preparation/src/main/kotlin/parameter/bind/BindPolicy.kt : classes a parameter tree may name
modules/preparation/src/main/kotlin/parameter/bind/BoundParameters.kt : compiled tree; varies, next()
modules/preparation/src/main/kotlin/parameter/bind/ParameterBinder.kt : compiles a parameter tree into a ValueNode
modules/preparation/src/main/kotlin/parameter/bind/ValueCoercion.kt : YAML value to constructor parameter type
modules/preparation/src/main/kotlin/parameter/bind/ValueNode.kt : tree nodes: Literal, Fresh, StaticField, Construction
modules/preparation/src/main/kotlin/parameter/resolve/Fingerprint.kt : first 8 hex chars of SHA-256
modules/preparation/src/main/kotlin/parameter/resolve/KeyFields.kt : keyBits and curve of a key, by key interface
modules/preparation/src/main/kotlin/parameter/resolve/PerInitValue.kt : whether an IvParameterSpec value is an IV or a constant the provider fills in
modules/preparation/src/main/kotlin/parameter/resolve/ResolvedParameters.kt : what the provider used after one call; key names
modules/preparation/src/main/kotlin/parameter/resolve/SpecFields.kt : fields of reported parameters, by spec class
modules/preparation/src/main/kotlin/port/Availability.kt : Available or Unavailable(reason)
modules/preparation/src/main/kotlin/port/DeviceCapability.kt : device port: providers, check, measuredKeyAlgorithm
modules/preparation/src/main/kotlin/prepare/CasePreparer.kt : one case: key, bind, input, one call, parameter read-back; a failure is a skip
modules/preparation/src/main/kotlin/prepare/ChartGroup.kt : which cases a chart may compare, from the service type, then the key kind
modules/preparation/src/main/kotlin/prepare/PreparedCase.kt : a built case: case, recipe, key, parameters, keyParameters, input, resolvedParameters; its chart group
modules/preparation/src/main/kotlin/prepare/PreparedRun.kt : prepared cases, skips, processRepetitions
modules/preparation/src/main/kotlin/prepare/StoppedOnFailureException.kt : thrown under onFailure stop
modules/preparation/src/main/kotlin/primitive/PrimitiveReader.kt : providers section to selections
modules/preparation/src/main/kotlin/record/PreparedDocument.kt : prepared.yaml document shape
modules/preparation/src/main/kotlin/record/PreparedFile.kt : writes prepared.yaml
modules/preparation/src/main/kotlin/report/Skip.kt : one skipped item (stage, provider, type, name, reason)
modules/preparation/src/main/kotlin/report/SkipFile.kt : writes skipped.yaml
modules/preparation/src/main/kotlin/request/BenchmarkRequest.kt : selections and global settings, validated
modules/preparation/src/main/kotlin/request/Selection.kt : one requested primitive entry, validated
modules/preparation/src/main/kotlin/resolve/CaseResolver.kt : selections to cases and rejections
modules/preparation/src/main/kotlin/resolve/Rejection.kt : one rejected selection or provider with reason
modules/preparation/src/main/kotlin/resolve/Resolution.kt : cases and rejections result
modules/preparation/src/main/kotlin/resolve/SelectionCheck.kt : per-selection rejection rules
modules/preparation/src/main/kotlin/resolve/SelectionExpander.kt : cartesian expansion of a selection into cases
modules/preparation/src/main/kotlin/shared/DocumentFields.kt : typed field reads with named errors
modules/preparation/src/main/kotlin/shared/DocumentFile.kt : YAML file read (schemaVersion check) and write
modules/preparation/src/main/kotlin/shared/YamlCodec.kt : SnakeYAML setup: safe load, no duplicate keys, indent 2
modules/preparation/src/test/kotlin/BenchmarkCaseTest.kt : case id and case validation tests
modules/preparation/src/test/kotlin/BenchmarkRequestTest.kt : request shape-error tests
modules/preparation/src/test/kotlin/CaseResolverTest.kt : expansion and rejection tests
modules/preparation/src/test/kotlin/ChartGroupTest.kt : chart group tests
modules/preparation/src/test/kotlin/CipherCallTest.kt : CipherCall repeat and re-init tests
modules/preparation/src/test/kotlin/DiscoveryCapabilityTest.kt : capture and trial availability tests
modules/preparation/src/test/kotlin/EffectiveFixture.kt : effective.yaml test fixture builder
modules/preparation/src/test/kotlin/EngineTypesTest.kt : engine type registry tests
modules/preparation/src/test/kotlin/ExampleFilesTest.kt : prepares example/ and compares the committed outputs
modules/preparation/src/test/kotlin/GlobalReaderTest.kt : run and policy read tests
modules/preparation/src/test/kotlin/InboundFileTest.kt : effective.yaml section and schema tests
modules/preparation/src/test/kotlin/InteropOracleTest.kt : interop verdict and plan-file tests
modules/preparation/src/test/kotlin/InvocationTest.kt : invocation repeatability and IV-reuse tests
modules/preparation/src/test/kotlin/KeyAlgorithmContractTest.kt : derived key names against a device trial's keyAlgorithm (-Dtrial)
modules/preparation/src/test/kotlin/KeyAlgorithmNameTest.kt : key name derivation tests
modules/preparation/src/test/kotlin/KeyMaterialGeneratorTest.kt : key generation tests
modules/preparation/src/test/kotlin/KeyPlannerTest.kt : key recipe planning tests
modules/preparation/src/test/kotlin/OperationContractTest.kt : per-operation consumption contract tests
modules/preparation/src/test/kotlin/OperationInputTest.kt : per-operation input tests
modules/preparation/src/test/kotlin/ParameterBinderTest.kt : parameter tree binding tests
modules/preparation/src/test/kotlin/PreparationFixture.kt : shared preparation test fixtures
modules/preparation/src/test/kotlin/PreparationPolicyTest.kt : onFailure policy tests
modules/preparation/src/test/kotlin/PreparedCaseTest.kt : prepared-case tests
modules/preparation/src/test/kotlin/PreparedFileTest.kt : prepared.yaml content tests
modules/preparation/src/test/kotlin/PrimitiveReaderTest.kt : providers-section read tests
modules/preparation/src/test/kotlin/ResolvedParametersTest.kt : read-back tests per parameter kind: GCM, CBC, key wrap, OAEP, PSS, EC curve, key size
```
