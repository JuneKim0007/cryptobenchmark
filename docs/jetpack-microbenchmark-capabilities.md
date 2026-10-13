# Jetpack Microbenchmark capability catalog

What `androidx.benchmark` (library `1.5.0`, this repo's pin — see `modules/android/build.gradle`)
actually gives us, and how each knob applies to *this* project (7 primitive types, 2 providers,
AndroidOpenSSL vs AndroidKeyStore). Sourced from official AndroidX docs, the sibling `../GOMES`
repo's working configuration, and this project's own earlier (pre-Jetpack) capstone drafts.
Confidence flag: ✅ confirmed against primary docs/source · ⚠ secondary-source only, verify before
relying on it.

AGP is pinned at `8.13.2` (`build.gradle`) — both this and the `benchmark-junit4` version are above
the `1.3.0-beta01` / AGP `8.4.0` threshold where microbenchmark force-AOT-compiles by default (§2).

---

## 1. Timing / metrics

| Capability | Where set | Controls | Default | Crypto relevance |
|---|---|---|---|---|
| `measureRepeated { }` ✅ | Kotlin, `BenchmarkRule` | the measured block; framework runs warmup then measurement | iterations auto-determined | wraps every AES/RSA/ECDSA/SHA op — already how `CryptoBenchmark.measure()` is written |
| `runWithMeasurementDisabled { }` ✅ | inside `measureRepeated` | excludes setup from the timed region | n/a | not used: each call pauses and resumes the timer (~40 ns/op measured on a Pixel 10: SHA-256 697 → 659 ns once removed); setup happens before `measureRepeated` instead |
| `state.pauseTiming()` / `resumeTiming()` (Java `BenchmarkState`) ✅ | direct calls | same purpose, Java-style loop | n/a | not needed — this repo is Kotlin-only |
| `state.keepRunningInline()` ✅ | `BenchmarkState` | reduces call overhead in tight loops | n/a | worth it for the cheapest cases (single SHA-256 block, HMAC on 64B) where method-call overhead is non-negligible relative to the op itself |
| Allocation count ✅ | automatic | GC pressure per op, reported alongside `timeNs` | always on | flags provider allocation differences (e.g. BouncyCastle vs AndroidOpenSSL) that would otherwise masquerade as pure timing differences |
| `androidx.benchmark.cpuEventCounter.enable` ✅ | instrumentation arg | hardware perf-counter collection (root required) | `false` | see [§11.1](#111-confirming-hardware-acceleration-is-real) |
| `androidx.benchmark.cpuEventCounter.events` ✅ | instrumentation arg | which counters: `Instructions`, `CPUCycles`, `L1DReferences`, `L1DMisses`, `BranchInstructions`, `BranchMisses`, `L1IReferences`, `L1IMisses` | `Instructions,CpuCycles,BranchMisses` | L1D counters directly relevant to table-based AES vs AES-NI comparison |
| `MetricCapture`/`TimeCapture` classes ⚠ | `androidx.benchmark` package | newer programmatic metric-capture API | — | possible extension point for a custom throughput metric; stable/public status unconfirmed |

**Not usable in microbenchmark** (macro-only, listed to avoid confusing the two APIs): `TraceSectionMetric`,
`PowerMetric` (needs a physical Pixel 6+, categories CPU/DISPLAY/GPU/GPS/MEMORY/ML/NETWORK —
this project's energy metric is ODPM rail energy from microbenchmark Perfetto traces, `tools/energy`; not `PowerMetric`, not E-Manafa), `StartupTimingMetric`,
`FrameTimingMetric`. Microbenchmark has a fixed metric set (time + allocations), not macro's
pluggable `metrics: List<Metric>`.

---

## 2. Compilation control (AOT/JIT)

**Key finding:** since `benchmark-junit4 ≥ 1.3.0-beta01` on `AGP ≥ 8.4.0`, microbenchmark
**force-AOT-compiles the test APK by default** — no config needed. This repo (`1.5.0` /
`8.13.2`) already gets it. `CompilationMode` (`Full`/`Partial`/`None`/`Ignore`/`DEFAULT`) is a
**macrobenchmark-only** concept and does not apply inside `measureRepeated`.

| Capability | Where set | Controls | Default here | Relevance |
|---|---|---|---|---|
| AOT-by-default ✅ | automatic (library/AGP version gated) | full AOT before measurement | **on**, unconfigured | RSA-4096 keygen and friends are not JIT-warming mid-measurement; no action needed |
| `androidx.benchmark.forceaotcompilation=false` ✅ | `gradle.properties` | opt **out** of the default | absent = on | could be flipped deliberately to A/B "JIT-warmed vs AOT" timings if warmup sensitivity itself becomes an RQ — not currently in scope |
| `androidx.benchmark.compilation.enabled=true` ✅ | instrumentation arg | GOMES sets this explicitly | — | **redundant on this repo's version** — GOMES pins the same behavior belt-and-suspenders; not needed here but harmless if added for explicitness |

---

## 3. Thermal / CPU control

| Capability | Where set | Controls | Default | Relevance |
|---|---|---|---|---|
| `./gradlew lockClocks` / `lockClocks.sh` ✅ | Gradle task or manual `adb push` + shell, rooted device only | pins CPU clocks, eliminates DVFS variance | off unless invoked | highest-value knob here — AES/RSA/ECDSA throughput is frequency-sensitive; **this repo does not currently invoke it, and neither does GOMES** (see §10) |
| Sustained Performance Mode ✅ | `Window.setSustainedPerformanceMode()`, automatic | stable lower max frequency, no root needed | **on by default** | fallback when devices aren't rooted (most CI/student devices) |
| Automatic thermal-throttle detection ✅ | built into the runner | detects throttling, sleeps, retries | always on | protects a long RSA-4096 sweep from silently reporting throttled numbers for later cases |
| `thermalThrottleSleepSeconds` (output field) ✅ | `benchmarkData.json`, per case | seconds slept for that case | 0 if none | already read in `JetpackResults.runtime()` (summed) — see [§11.3](#113-catching-a-throttled-outlier-before-it-pollutes-rq2) for why it should also be checked per-case, not just summed |
| `suppressErrors=UNLOCKED` ✅ | instrumentation arg | downgrades the "clocks unlocked" hard-error to a warning | not suppressed | only use deliberately; GOMES suppresses it project-wide (§10) — don't inherit that silently |

---

## 4. Profiling

Set via `androidx.benchmark.profiling.mode` (`None`/`MethodTracing`/`StackSampling` — confirmed;
no `Connected`/`MethodTracingAndSampling` mode exists ✅). Profiling always runs as a **separate
sequential pass** after the measured pass — it never pollutes the reported numbers, but roughly
doubles wall-clock run time, so it's for targeted inspection, not the full sweep.

| Mode | Captures | Extra args | Crypto relevance |
|---|---|---|---|
| `None` ✅ | timing + allocations only | — | use for the actual measurement sweep that produces reported numbers |
| `MethodTracing` ✅ | full Java/Kotlin method entry/exit trace | — | shows `Cipher.doFinal()` as one opaque frame — not useful for AndroidOpenSSL, whose real work is native |
| `StackSampling` ✅ | periodic stack samples, **includes native/C++ frames via simpleperf on Android 10+** | `sampleFrequency` (default 1000 Hz), `sampleDurationSeconds` (default 5s), `skipWhenDurationRisksAnr` (default `true`) | best choice here — AndroidOpenSSL is a Java wrapper over native BoringSSL; only StackSampling can attribute time into the native AES-NI/GHASH frames — see [§11.2](#112-proving-the-time-is-actually-in-native-crypto-code) |
| `ProfilerConfig.MethodTracing`/`StackSampling` (code-level) ⚠ | same, per-test not global | — | lets you profile only RSA keygen without a global instrumentation-arg sweep-wide flag |

---

## 5. Output / reporting

| Field / flag | Where | Notes |
|---|---|---|
| `androidx.benchmark.output.enable` ✅ | instrumentation arg | keep on (default `true`) — primary data source |
| `additionalTestOutputDir` ✅ | instrumentation arg | override on-device output path if not using Gradle's default pull |
| `benchmarkData.json` → `context` block ✅ | output file | `build.model/fingerprint/version.sdk`, `cpuCoreCount`, `cpuLocked`, `cpuMaxFreqHz`, `memTotalBytes`, `sustainedPerformanceModeEnabled` — already read by `JetpackResults.runtime()` |
| `benchmarkData.json` → per-case entry ✅ | output file | `name`, `params`, `totalRunTimeNs`, `warmupIterations`, `repeatIterations`, `thermalThrottleSleepSeconds`, `metrics.timeNs.{minimum,maximum,median,runs[]}` |
| `metrics.timeNs.runs[]` ✅ | output file | the **raw per-iteration array** — already captured as `CaseMeasurement.nanosPerOperation`, which is what IQR/percentiles/Mann-Whitney U need, not just `median` |

---

## 6. CI / dry-run / suppression

| Capability | Default | Relevance |
|---|---|---|
| `androidx.benchmark.dryRunMode.enable` ✅ | `false` | one loop, no real measurement — use to smoke-test a newly added benchmark case before burning device time |
| `androidx.benchmark.iterations` ✅ | **`50`** | matches this repo's `HarnessSettings.iterations` field *and* matches the Feb-2026 capstone draft's "50 measured iterations (configurable)" — three independent sources agree; the May-2026 abstract's "50,000 inner-loop iterations" is a **different, pre-Jetpack convention** — see [§12](#12-harness-mechanics-from-the-capstone-papers-reconcile-dont-port) |
| `androidx.benchmark.suppressErrors` ✅ | none suppressed | values: `DEBUGGABLE, LOW-BATTERY, EMULATOR, CODE-COVERAGE, UNLOCKED, SIMPLEPERF, ACTIVITY-MISSING` — never suppress `EMULATOR` for numbers that go in the paper; GOMES suppresses it for CI convenience (§10), that's a CI-only trade-off, not a measurement-run one |
| `androidx.benchmark.killExistingPerfettoRecordings` ✅ | `true` | prevents an orphaned trace from a crashed profiling run corrupting the next |
| `listener=androidx.benchmark.junit4.SideEffectRunListener` ✅ | not set | suppresses background OS noise (notifications, sync) during the run — worth enabling for lab/device runs |
| Device-state validation gate ✅ | enforced | hard-fails unless suppressed if: debuggable, emulator, clocks unlocked (on rooted devices), battery <25% — treat a failure as a stop, not something to retry through |

---

## 7. Gradle plugin config

Confirmed ✅: plugin id `androidx.benchmark`; required
`testInstrumentationRunner = "androidx.benchmark.junit4.AndroidBenchmarkRunner"` (already set,
`modules/android/build.gradle:16`); `buildTypes { debug { isDebuggable = false } }`; AGP 8.3+
`buildTypes.release.androidTest.enableMinification = true`.

Unconfirmed ⚠ (found only via secondary search, not primary source — verify against
`BenchmarkPlugin.kt` before relying on these): a top-level `benchmark { }` DSL block,
`enableGarbageCollectionMetric`, `outputDatabaseSchema`, `perfettoMode`.

---

## 8. This repo vs GOMES — same library, different choices

| Knob | This repo (`cryptobenchmark`) | GOMES | Takeaway |
|---|---|---|---|
| Parameterization | `@RunWith(Parameterized::class)`, **constructor injection** — one `PreparedCase` per JUnit instance | one `@Test` method per variant, manual stacking (no `Parameterized` anywhere) | two valid real-world patterns; this repo already committed to injection, which scales better for ~176+ algorithm×provider×size combinations than hand-written per-variant methods |
| AOT control | implicit (version-gated default, §2) | explicit: `compilation.enabled=true` **and** `gradle.properties` `forceaotcompilation=true` | GOMES is redundant/explicit; this repo relies on the same default silently — worth making explicit too, for readability if nothing else |
| Clock lock | not invoked | **not invoked** — instead suppresses the unlocked-clock error (`suppressErrors=UNLOCKED`, `cpuClockLock=false`) | neither project locks clocks; GOMES's choice is deliberate (run on stock unrooted devices) — this repo hasn't stated a position yet, and should, since it's the single highest-value knob for CPU-bound crypto timing (§3) |
| R8/minification | `minifyEnabled false` (`modules/android/build.gradle`) | `isMinifyEnabled = true`, `testBuildType = "release"`, with proguard rules specifically keeping reflection-based (de)serialization models | AndroidX's own guidance runs microbenchmarks against minified release for realism; this repo currently doesn't — a gap, not yet a decision |
| Profiling mode | unset (library default) | explicitly left unset/removed (comment: "so Benchmark 1.5.x can apply its repaired trace configs") | same effective choice, GOMES just documents why |
| Dead-code guard | `BlackHole.consume()` (`run/BlackHole.kt`) | `androidx.benchmark.BlackHole.consume()`, same API | identical — this repo already tracks the current AndroidX API, not the deprecated pattern |
| Orchestration | Kotlin/Gradle-native | Python (`run_suite.py`) drives one Gradle invocation per benchmark **class** via `-Pandroid.testInstrumentationRunnerArguments.class=<FQCN>`, pulls `benchmarkData.json` + trace per class | GOMES's one-class-per-invocation dispatch keeps each pulled JSON/trace pair unambiguous — a pattern worth considering if this repo's orchestration ever needs to interleave profiling runs with measurement runs |

---

## 9. Macro-only capabilities (for completeness, not directly usable here)

`CompilationMode.{Full,Partial,None,Ignore,DEFAULT}`, `PowerMetric`, `TraceSectionMetric`,
`StartupTimingMetric`, `FrameTimingMetric`, `MacrobenchmarkRule`. These matter only if this
project ever adds a macrobenchmark suite on top of the microbenchmark one (e.g., measuring a
crypto-heavy screen's cold-start cost) — not applicable to the current per-primitive timing work.

---

## 10. Worked examples

### 10.1 Confirming hardware acceleration is real

RQ1 asks whether AndroidOpenSSL's `AES/GCM` measurably uses AES-NI versus ChaCha20's pure-ARX
software path. Enabling `androidx.benchmark.cpuEventCounter.events=Instructions,CPUCycles,L1DReferences,L1DMisses`
(root required) on both cases and using the resulting cycles-per-byte and L1D-miss-rate columns,
we'd expect to find AES/GCM burning far fewer cycles/byte with a flat miss profile (fixed-function
hardware, no table lookups) while ChaCha20 shows a different but table-lookup-independent profile —
turning "provider X is faster" into "provider X is faster because it bypasses the ALU/cache path,"
which is the mechanism RQ1 actually asks about, not just the symptom.

### 10.2 Proving the time is actually in native crypto code

AndroidOpenSSL wraps native BoringSSL. Using `StackSampling` (not `MethodTracing`, which would
show `Cipher.doFinal()` as one opaque Java frame) on the `AES/GCM` case, we'd expect the majority
of samples to land inside native AES-NI/GHASH intrinsics rather than JNI marshalling — using this
we can validate that a measured latency difference between AndroidOpenSSL and AndroidKeyStore is a
genuine crypto-engine difference, not JNI/Binder overhead from the AndroidKeyStore round-trip.

### 10.3 Catching a throttled outlier before it pollutes RQ2

A full sweep runs SHA-1 through RSA-4096 keygen back-to-back. If the device throttles two-thirds
through (RSA keygen is the slow, CPU-bound case most likely to trigger it), `thermalThrottleSleepSeconds`
on the later cases will be nonzero while the earlier SHA/HMAC cases show 0 — using this per-case
field (not just the summed total `JetpackResults.runtime()` currently reports) we can flag that an
"RSA keygen is disproportionately slow on this device" finding in RQ2's per-algorithm ranking might
actually be "RSA keygen ran under thermal throttling," and needs a clean re-run before publication.

### 10.4 AOT is already on, so don't re-solve a solved problem

This repo pins `benchmark-junit4:1.5.0` on AGP `8.13.2`, both above the threshold where
microbenchmark force-AOT-compiles by default. Using that fact, we find the project doesn't need
`androidx.benchmark.compilation.enabled=true` or a `forceaotcompilation` gradle.properties flag —
GOMES sets both anyway (redundant on this version), but on this repo's stack it's already covered
by the library default, so there's nothing to add here.

### 10.5 Dry-run for dev speed, never for a reported number

Adding a new Ed25519 signature case: run it once with `androidx.benchmark.dryRunMode.enable=true`
to confirm the `PreparedCase` wiring works end-to-end in seconds, not the full ~50-iteration
measured run. Using dry-run here catches a broken case before burning device time — but real
reported numbers must never run with `suppressErrors=EMULATOR`; GOMES's macro module suppresses it
for CI convenience, which is fine for a jank-detection macrobenchmark but would silently produce
meaningless AES-NI-absent numbers if reused uncritically for a hardware-acceleration RQ here.

---

## 11. Harness mechanics from the capstone papers — reconcile, don't port

Found while mining `~/Desktop/capstone/my_capstone_abstract.md` and `capstone_approaches.md`
(pre-Jetpack drafts, written for a manual JUnit + E-Manafa harness, not `androidx.benchmark`):

| Draft convention | Conflicts with | Verdict |
|---|---|---|
| 50,000 raw inner-loop calls inside one `BENCH_START`/`BENCH_END` window | Jetpack's `androidx.benchmark.iterations` (default 50, §6) already models "iteration count" as the outer measured-call count, with its own warmup/thermal/percentile machinery built around **one measured call = one iteration** | don't port the 50,000-batch; let Jetpack's `iterations` (overridable via `HarnessSettings`) be the count — stacking 50,000 calls inside a single measured iteration would collapse per-op percentile/outlier detection into one blended number |
| 10 warmup iterations, discard first 3 of 30 measurement runs (manual JIT protocol, borrowed from Rua & Saraiva) | superseded by Jetpack's `WarmupManager` (moving-average convergence, §2) | non-adoption — this is what Jetpack's warmup phase already does, better |
| Batch-of-10 structure for the cache-pressure sweep (re-warms the working set between ops) | no direct Jetpack equivalent — `measureRepeated` runs one logical op per iteration | a genuine design decision if a cache-pressure RQ is ever added (not currently in `docs/cryptography/primitives.md`'s benchmark scope); would require nesting N calls inside one `measureRepeated` block, changing what "one iteration" means for reported percentiles — flag explicitly if adopted, don't do it silently |
| JMH-style geometric mean of normalized throughput (`capstone_approaches.md` §6.1) | AndroidX Microbenchmark reports median/mean/CoV per iteration natively, not geomean-of-throughput-across-forks (that's a JVM/JMH concept, ART doesn't fork) | if wanted, compute as a post-hoc analysis layer over the raw `benchmarkData.json`/`nanosPerOperation`, not requested from Jetpack itself |

The open question already logged in `docs/benchmark-methodology.md` — does the default iteration
count give Mann-Whitney U enough samples — has a partial answer from the *Statistically Rigorous
Android Macrobenchmarks* blog cited there: **>30 iterations** before CI math is valid, and halving
CI width costs **9x** the iterations. The default `50` clears the 30-sample floor; tightening the
CI further gets expensive fast.
