# Refactor backlog

Surveyed 2026-09-21 · scope modules/benchmark + modules/environment/discovery · 92 files
Baseline: tests 65 green · 2897 lines · 107 comment lines
Tests run: root `./gradlew` cannot configure (jcenter `hunter-transform:0.9.3` gone). Baseline from `tools/jca-contract` (discovery, 37) and a scratchpad build over the benchmark sources (28) at HEAD 5fc00f7.

## Open

### R1 · Dead code · discovery/setting/ (7 files)
status   planned — ASK a
evidence 0 main refs; 1 consumer, JcaContractTest:87-93 asserts it agrees with CaptureQuery; docs.md:34 and probe.md:3,14 document it as a stage
remedy   delete -> unlink JcaContractTest:10,23,43,87-93, Playground.kt:5,83,88, docs, then the 7 files
expect   -133 lines, ≈-15 test lines; closes clump (model…release), ServiceLookup≈ServiceIndex, Device≈RuntimeInfo, 2 chains, BenchmarkScope
blocked  answer to ASK a (recommend delete: discovery reports capability, setup owns the knobs)
first seen 2026-09-21

### R2 · Primitive obsession · engine type as String
status   planned — ASK b
evidence 15 fold call sites over 2 definitions (EngineTypeName, ServiceKey.fold); 3 tables (AxisRules 7, KeyShapes 8, BenchmarkScope 7 keys); "Cipher" literal at 6 sites; KeyAlgorithmName.of 4-arm `when`
remedy   EngineType across both modules changes equality of BenchmarkCase.type/Selection.type; generic registry dropped by principles (R30). Recommend leave
expect   none scheduled
blocked  answer to ASK b
first seen 2026-09-21

### R3 · Primitive obsession · failure reason as coded String
status   planned — ASK c
evidence 12 literals in 5 files; 18 test assertions compare them; only not_registered ×2 (DiscoveryCapability) and no_key_generator ×2 (KeyPlanner) repeat in a module
remedy   2 private constants, or leave. TrialRunner:31 "provider_not_installed" is a wire value, not a duplicate
expect   ≈-0 lines
blocked  answer to ASK c
first seen 2026-09-21

### R4 · Data clump · (provider, type, algorithm)
status   deferred
evidence 8 sites in 2 modules; `algorithm` vs `algorithmOrAlias` differ in meaning; ServiceKey is internal to discovery
remedy   Introduce Parameter Object -> refactor-simplifying-method
expect   port signature change, 3 test doubles edited
blocked  R2 answered
safety   RECONSIDER
first seen 2026-09-21

### R5 · Parallel hierarchies · KeyShape / KeyRecipe / KeyMaterial
status   deferred
evidence 3 matched name pairs, 5 edit sites per new key kind; 1 commit of history (5fc00f7); (algorithm, keySize, provider) repeated in KeyRecipe.Secret and .Pair
remedy   Move Field (fold KeyShape into KeyRecipe) -> refactor-moving-feats-btw-objects
expect   -1 enum, 1 `when` reshaped; KeyPlannerTest:63 edited
blocked  a second key kind landing
safety   RECONSIDER
first seen 2026-09-21

### R6 · Duplicate code · Environment/ProviderClassName/TrialYamlWriter
status   planned
evidence toYaml, fileName, write and the (directory, codec) constructor identical in 3 files; 4 window collisions; changed together in c95706e and b66754e
remedy   Form Template Method, shared base, class names and constructors kept -> refactor-dealing-with-generalization
expect   60 -> ≈35 lines; probe_/probe_classes_/trial_<utc>.yaml byte-identical
blocked  none
safety   SAFE (verify: dump the 3 files before and after, diff bytes, then suite)
first seen 2026-09-21

### R7 · Comments · workload/StringType.java
status   planned
evidence 13 of 80 lines: 6 comment lines restating the next statement, 7-line commented-out block at 72-78
remedy   delete -> refactor-non-pattern
expect   -13 comment lines
blocked  none
safety   SAFE
first seen 2026-09-21

### R8 · Dead code · discovery/temp.md + 5 signature-restating comment lines
status   planned
evidence grep -F 'temp.md' = 0 hits; header "not part of the module docs"; comments: TrialQuery:8,21, Rejection:5, ServiceEntry:4, CaptureQuery:35 (duplicates ServiceTree:9)
remedy   delete -> refactor-non-pattern
expect   -203 doc lines, -5 comment lines
blocked  none
safety   SAFE
first seen 2026-09-21

### R9 · Dead code · workload/DataType.java static stubs + StringType.gen* duplicate
status   deferred
evidence 4 static methods returning null, `grep 'DataType\.gen'` = 0 hits; gen and genPseudo 13 lines each identical bar `new Random(seed)`; 15 :android files use StringType
remedy   delete stubs; Extract Method -> refactor-composing-method
expect   -11 lines, ≈-13 lines
blocked  a working :android build (root gradle broken)
safety   RECONSIDER
first seen 2026-09-21

### R10 · Dead code · adapter/DeviceRuntimeReader.kt
status   deferred
evidence 0 code refs, 1 commented-out (Playground.kt:68), 7 doc refs; only producer of RuntimeInfo's 5 device fields
remedy   none: NOT deletable until the :android caller exists
expect   -26 lines if ever removed
blocked  :android wiring
first seen 2026-09-21

### R11 · Dead code · decode half of CaptureDocument, TrialDocument, DocumentFields, YamlCodec.load
status   deferred
evidence 0 main callers, 8 test refs; nothing reads a capture or trial back from YAML; commit 39e92c5 made the round trip on purpose
remedy   none: NOT deletable while DiscoveryCapability needs a file loader
expect   ≈-108 lines if ever removed
blocked  loader decision
first seen 2026-09-21

### R12 · Speculative generality · query surface with no production caller
status   deferred
evidence CaptureQuery.namesOf, onlyOn; TrialQuery.failingServices, failingTransformations, instantiationByProvider (returns bare Pair<Int, Int>); TransformationFailure; 8 test refs, 9 doc refs
remedy   delete or keep as documented API
expect   ≈-28 lines
blocked  decision: documented queries, kept or dropped
first seen 2026-09-21

### R13 · Speculative generality · contract fields nothing reads
status   deferred
evidence BenchmarkRequest.processRepetitions (validated, never copied to a case); Metric.ALLOCATION and CPU_EVENTS 0 refs; BenchmarkCase.seed copied only
remedy   none until the harness exists
expect   ≈-5 lines
blocked  harness not written
first seen 2026-09-21

### R14 · Speculative generality · unused constructor parameters
status   deferred
evidence KeyMaterialGenerator.fallback (2 callers, 0 pass it); Discovery(providerProbe, trialRunner, codec) (2 callers, 0 pass them)
remedy   Remove Parameter -> refactor-simplifying-method
expect   ≈-4 lines
blocked  thin history (5fc00f7); Discovery's injection is documented (c834388)
safety   RECONSIDER
first seen 2026-09-21

### R15 · Primitive obsession · KeyMaterial.Pairs positional list
status   unverified
evidence comment "own pair first, peer second"; the only reader is KeyMaterialGeneratorTest:29-33
remedy   Replace Data Value with Object once a production reader exists
expect   n/a
blocked  a production consumer
first seen 2026-09-21

## Done

## Dropped

### R16 · Feature envy · measurement/CaseName.kt
dropped 2026-09-21 — id format is the instrumentation test name (BenchmarkCaseTest:11,15,21), own file by design (0a69df6)

### R17 · Message chain · service.attributes.supportedModes/supportedPaddings
dropped 2026-09-21 — 4 one-token edits against 2 new forwarding members

### R18 · Data clump · DeclaredAlias = AliasEntry
dropped 2026-09-21 — AliasEntry validates non-blank in init and DeclaredAlias does not; merging changes what a malformed alias raises

### R19 · Primitive obsession · transformation string
dropped 2026-09-21 — 3 one-line sites across 2 modules; a class for them is a lazy class

### R20 · Data class · TrialOutcome status()/failed
dropped 2026-09-21 — 2 duplicated 1-line expressions; net +1 line and one more hop; `it.outcome.failed` is still 2 links

### R21 · Long method · ProviderProbe.toEntry
dropped 2026-09-21 — extraction keeps the same total lines, nesting 3 to 2, one file; not measurably simpler

### R22 · Long method · PropertyKeyParser.classify
dropped 2026-09-21 — 34 lines, flat prefix dispatch, under threshold

### R23 · Long parameter list · SelectionExpander.expand
dropped 2026-09-21 — `rule` derives from `rules`, which the expander does not hold; 1 caller

### R24 · Lazy class · SelectionExpander, TransformationSet, KeyAlgorithmName
dropped 2026-09-21 — one responsibility per file is the convention (c95706e); each holds 13-25 lines of logic

### R25 · Divergent change · ProviderProbe.kt, PropertyKey.kt
dropped 2026-09-21 — 12 of 13 commits predate the split at c95706e and 46afe99

### R26 · Data class · CapturedEnvironment precedence sort at 3 sites
dropped 2026-09-21 — serialised contract documented as "holds no logic"; queries own the questions

### R27 · Duplicate code · schema-version gate and SCHEMA_VERSION ×3
dropped 2026-09-21 — capture, trial and setting schemas evolve independently; coincidence, not duplication

### R28 · Primitive obsession · keySize/inputSize validation at 2 sites each
dropped 2026-09-21 — each pair validates a different shape (list vs scalar) at its own layer boundary

### R29 · Middle man · the three YAML writers
dropped 2026-09-21 — facade over document, codec, file name and directory; the duplication is R6

### R30 · Duplicate code · AxisRules ≈ KeyShapes as a generic registry
dropped 2026-09-21 — names pinned by 3 tests, so wrappers would forward to the registry; the saving disappears

## Refused

### R31 · Strategy · engine-type rules
refused — tables and 1-line transforms; Strategy adds 3 classes to hold them

### R32 · Template Method (pattern) · YAML writers
refused — R6's shared base is the technique; no abstract hierarchy needed

### R33 · Visitor · KeyShape / KeyRecipe / KeyMaterial
refused — hierarchy is 1 commit old and growing, not stable

### R34 · State / Strategy · failure reasons
refused — codes carry no behaviour
