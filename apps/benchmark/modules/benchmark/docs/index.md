# benchmark

```
apps/benchmark/modules/benchmark/.gitignore : ignores /build
apps/benchmark/modules/benchmark/README.md : module summary and link to this index
apps/benchmark/modules/benchmark/build.gradle : Kotlin/JVM 17 library; api :preparation; snakeyaml 2.3; passes examples.update to tests
apps/benchmark/modules/benchmark/docs/check.md : the end-to-end check: one call per case, oracles, measured decisions, check.yaml, the diff
apps/benchmark/modules/benchmark/docs/index.md : this map
apps/benchmark/modules/benchmark/docs/measure.md : plan check, host harness, benchmark.json, merge, Jetpack conversion
apps/benchmark/modules/benchmark/example/benchmark_jetpack_example.json : example androidx benchmarkData.json
apps/benchmark/modules/benchmark/example/benchmark_prepared_example.yaml : prepared.yaml paired with the Jetpack example
apps/benchmark/modules/benchmark/src/main/kotlin/RefusedPlanException.kt : a run-wide refusal, or no case left, from PlanCheck.runnable
apps/benchmark/modules/benchmark/src/main/kotlin/check/EnergyCapability.kt : parses energy.yaml; derives the energy refusal
apps/benchmark/modules/benchmark/src/main/kotlin/check/PlanCheck.kt : pre-preparation refusals for the listed cases; the runnable cases with the refused ones left out, and those as skips
apps/benchmark/modules/benchmark/src/main/kotlin/check/Refusal.kt : one refusal (caseId, reason)
apps/benchmark/modules/benchmark/src/main/kotlin/check/RunnablePlan.kt : the orchestrator's side: listing, plan check, one case prepared at a time, any throw that case's logged skip; the one writer of skipped.yaml and prepared.yaml
apps/benchmark/modules/benchmark/src/main/kotlin/report/BenchmarkJson.kt : writes benchmark.json text
apps/benchmark/modules/benchmark/src/main/kotlin/report/CaseDocument.kt : shared YAML and JSON reader for case documents
apps/benchmark/modules/benchmark/src/main/kotlin/report/Merge.kt : merges per-process benchmark.json texts; a case that cannot merge is left out with a line
apps/benchmark/modules/benchmark/src/main/kotlin/report/MetricKeys.kt : run.metrics entry to its benchmark.json metric keys
apps/benchmark/modules/benchmark/src/main/kotlin/report/MetricSamples.kt : one metric's runs, iteration count, reported stats; metric key names
apps/benchmark/modules/benchmark/src/main/kotlin/report/PassMerge.kt : one row per case from per-pass files; each owned metric only from its pass
apps/benchmark/modules/benchmark/src/main/kotlin/report/ReportedStats.kt : androidx minimum, maximum, median, CoV for one process
apps/benchmark/modules/benchmark/src/main/kotlin/report/ResultRow.kt : one case row of benchmark.json
apps/benchmark/modules/benchmark/src/main/kotlin/report/energy/EnergyWindows.kt : reads energy.json into energyJ samples and per-case reasons a case is not joined
apps/benchmark/modules/benchmark/src/main/kotlin/report/jetpack/JetpackResults.kt : benchmarkData.json and prepared.yaml to rows, runtime and the dropped cases' lines
apps/benchmark/modules/benchmark/src/main/kotlin/report/jetpack/RunCountAudit.kt : compares requested iterations and allocation runs to actual runs
apps/benchmark/modules/benchmark/src/main/kotlin/run/BlackHole.kt : result sink
apps/benchmark/modules/benchmark/src/main/kotlin/run/CaseMeasurement.kt : one host-measured case: timeNs samples, median
apps/benchmark/modules/benchmark/src/main/kotlin/run/CaseRun.kt : fun interface run(): Long?
apps/benchmark/modules/benchmark/src/main/kotlin/run/CaseSettings.kt : harness settings as plain values, no androidx type
apps/benchmark/modules/benchmark/src/main/kotlin/run/HostHarness.kt : host JVM timing loop; ONCE, the check's one untimed call
apps/benchmark/modules/benchmark/src/main/kotlin/run/OneCall.kt : fun interface call(invocation, hook): one untimed call through a harness
apps/benchmark/modules/benchmark/src/main/kotlin/run/OutputHook.kt : check mode only: the outputs a call handed over, never built by a timed run
apps/benchmark/modules/benchmark/src/main/kotlin/run/SampleCleaning.kt : the host loop's forced GC and finalization before each sample, the pause and GC count reported beside the time
apps/benchmark/modules/benchmark/src/main/kotlin/run/TimedLoop.kt : calls once() until a nanosecond budget is spent; returns the call count
apps/benchmark/modules/benchmark/src/main/kotlin/run/compose/CaseRuns.kt : composes a CaseRun from the energy capture mode
apps/benchmark/modules/benchmark/src/main/kotlin/run/decorate/Cooldown.kt : sleeps after the inner run
apps/benchmark/modules/benchmark/src/main/kotlin/run/decorate/EnergyWindow.kt : brackets the inner run with an energy:<id> marker
apps/benchmark/modules/benchmark/src/main/kotlin/run/decorate/Rewarm.kt : TimedLoop warm-up before the inner run
apps/benchmark/modules/benchmark/src/main/kotlin/run/energy/Energy.kt : energy settings with defaults
apps/benchmark/modules/benchmark/src/main/kotlin/run/energy/WindowMarker.kt : begin and end marker port
apps/benchmark/modules/benchmark/src/main/kotlin/verify/CaseCheck.kt : one case end to end: its invocation, one harness call, what it did, every oracle; the oracles strongest first
apps/benchmark/modules/benchmark/src/main/kotlin/verify/OutputBytes.kt : a call's output as bytes and their SHA-256
apps/benchmark/modules/benchmark/src/main/kotlin/verify/known/KnownAnswer.kt : one sourced vector and which cases it matches
apps/benchmark/modules/benchmark/src/main/kotlin/verify/known/KnownAnswerFile.kt : reads known-answers.yaml; hex inside parameter trees to bytes
apps/benchmark/modules/benchmark/src/main/kotlin/verify/known/RawMaterial.kt : check mode only: a case with the vector's raw key, fixed parameters and input
apps/benchmark/modules/benchmark/src/main/kotlin/verify/observe/ObservedCall.kt : what one call did (steps, a new engine or not, inits per call, IV, key origin), read before and after it
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/ContractOracle.kt : the operation's contract properties over the output
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/CrossProviderOracle.kt : every other provider of the case's service checks the call's own output; the peer check per operation
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/KnownAnswerOracle.kt : the case's invocation over a vector, its output against the source
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/NonceOracle.kt : encrypt that re-inits with a drawn IV shows a new IV each call
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/Oracle.kt : Oracle, CheckedCall, Judgement
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/PlanOracle.kt : one harness call whose observed steps are what perCall plans
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/AgreeProperties.kt : the peer derives the same secret
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/DecryptProperties.kt : the seeded plaintext returns; a tag refuses tampering
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/DigestProperties.kt : declared length and the same output from the call replayed with its drawn parameters, for digests and MACs
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/EncryptProperties.kt : size bound, the same provider's decrypt recovers the input, a tag refuses tampering
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/KeyOutputProperties.kt : a key of the asked kind and size, a new one each call
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/Properties.kt : fun interface of one operation's named properties; shared helpers
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/SignProperties.kt : the provider verifies its signature and refuses it over a changed message
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/Tamper.kt : a changed ciphertext refused where a tag length was read back
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/contract/VerifyProperties.kt : verify was true in the call; a changed signature is refused
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/cross/CipherPeer.kt : the peer decrypts the case's ciphertext to its input, or the same ciphertext to its output
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/cross/KeyOutputPeer.kt : the peer's KeyFactory rebuilds a generated key pair, the public half to the same encoding
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/cross/PeerCheck.kt : PeerCheck, PeerRefusal; setup the peer refuses is not_checkable, a refused or contradicted output fails
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/cross/PeerKey.kt : the case's key rebuilt by the peer's KeyFactory from its encoding; peer_key_rejected
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/cross/PeerParameters.kt : the parameters the call used, from the engine's report or the case's fixed spec, in a form another provider takes
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/cross/RecomputePeer.kt : the peer recomputes a digest, MAC or agreed secret from the same key, parameters and input
apps/benchmark/modules/benchmark/src/main/kotlin/verify/oracle/cross/SignaturePeer.kt : the peer verifies the case's signature, or accepts what the case accepted
apps/benchmark/modules/benchmark/src/main/kotlin/verify/record/CaseRecord.kt : one case of check.yaml: plan, observed, outcome, verdicts, digest; not-run cases with their reason
apps/benchmark/modules/benchmark/src/main/kotlin/verify/record/CheckFile.kt : writes and reads check.yaml with its summary
apps/benchmark/modules/benchmark/src/main/kotlin/verify/record/RecordDiff.kt : two check.yaml case lists to every difference
apps/benchmark/modules/benchmark/src/test/kotlin/BenchmarkJsonRoundTripTest.kt : benchmark.json write, read and merge round-trip tests
apps/benchmark/modules/benchmark/src/test/kotlin/CaseCheckTest.kt : end-to-end case check: verdicts, observed steps, one call, errors
apps/benchmark/modules/benchmark/src/test/kotlin/CaseDocumentTest.kt : case document reader tests
apps/benchmark/modules/benchmark/src/test/kotlin/CaseRecordTest.kt : not-run ids independent of skip order; reasons without identity hashes
apps/benchmark/modules/benchmark/src/test/kotlin/CaseSettingsTest.kt : HarnessSettings to CaseSettings tests
apps/benchmark/modules/benchmark/src/test/kotlin/CheckFixture.kt : JDK prepared cases, a capability without peers and one with PeerProvider for the check tests
apps/benchmark/modules/benchmark/src/test/kotlin/CheckModeTest.kt : the output hook absent from every timed path; ONCE hands one output
apps/benchmark/modules/benchmark/src/test/kotlin/CorruptedOutputTest.kt : knownAnswer, crossProvider and contract each fail an output with one flipped byte, also through CaseCheck; the honest call passes them
apps/benchmark/modules/benchmark/src/test/kotlin/CrossProviderOracleTest.kt : the peer recomputes the call's own output; a key it cannot rebuild is peer_key_rejected
apps/benchmark/modules/benchmark/src/test/kotlin/DigestPropertiesTest.kt : a Mac random by bug fails the repeat with fixed or per-call parameters; a nonce-keyed one passes
apps/benchmark/modules/benchmark/src/test/kotlin/EnergyCheckTest.kt : energy refusal and energyJ join tests
apps/benchmark/modules/benchmark/src/test/kotlin/EnergyRunTest.kt : CaseRuns composition tests
apps/benchmark/modules/benchmark/src/test/kotlin/FakeMacProvider.kt : a test provider with two GMAC-named Macs: random by bug, and keyed by its nonce, for the repeat property
apps/benchmark/modules/benchmark/src/test/kotlin/HostHarnessTest.kt : host loop tests
apps/benchmark/modules/benchmark/src/test/kotlin/JetpackResultsTest.kt : Jetpack conversion tests over example/
apps/benchmark/modules/benchmark/src/test/kotlin/KnownAnswerFileTest.kt : the vector catalogue: sources, matching, hex, unknown fields
apps/benchmark/modules/benchmark/src/test/kotlin/MergeTest.kt : per-process merge tests
apps/benchmark/modules/benchmark/src/test/kotlin/PassMergeTest.kt : per-pass merge tests
apps/benchmark/modules/benchmark/src/test/kotlin/PeerProvider.kt : a test provider delegating SHA-256 and HmacSHA256 to the JDK's, the cross-provider peer
apps/benchmark/modules/benchmark/src/test/kotlin/PlanCheckTest.kt : refusal tests
apps/benchmark/modules/benchmark/src/test/kotlin/RecordDiffTest.kt : no difference between equal runs; every added, removed and changed field
apps/benchmark/modules/benchmark/src/test/kotlin/RunCountAuditTest.kt : run-count audit tests
apps/benchmark/modules/benchmark/src/test/kotlin/RunnablePlanTest.kt : the orchestrator loses only the failing case: preparation and later-stage throws as logged skips, both files, onFailure stop
apps/benchmark/modules/benchmark/src/test/kotlin/ThrowingProvider.kt : test provider: SHA-256 under names that throw AssertionError, StackOverflowError or IllegalStateException while armed
```
