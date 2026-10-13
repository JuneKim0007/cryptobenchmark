# Jetpack Microbenchmark configuration catalog

How *this project* configures `androidx.benchmark`, split into global (harness-wide) vs
target-specific (per-case) settings — as distinct from
[jetpack-microbenchmark-capabilities.md](jetpack-microbenchmark-capabilities.md), which catalogs
what the library can do in general. This file is the applied side: what we set, where, and why.

The codebase's own convention is already "global unless an entry states otherwise" —
`HarnessSettings` is mergeable, `Override.harness` overrides it per test-set rule
(`modules/config/src/main/kotlin/testset/dto/Override.kt`).

---

## Table A — Global harness configuration

Applies to every case unless a `testset` rule's `Override.harness` states otherwise.

| Setting | Jetpack mechanism | Repo field | Status |
|---|---|---|---|
| Parameterization method | JUnit4 `@RunWith(Parameterized::class)`, **constructor injection** — not a loop stacking multiple cases inside one `@Test` | `CryptoBenchmark(caseId, prepared: PreparedCase)` | **decided, implemented**: one JUnit test instance per `PreparedCase` → one row per case in `benchmarkData.json`, named `measure[<caseId>]`. GOMES uses the opposite pattern (one `@Test` method per variant, no `Parameterized`) — see capabilities.md §8 for the comparison; this repo's choice scales better for ~176+ algorithm×provider×size combinations |
| Measured iterations | `BenchmarkRule.measureRepeated` count / `androidx.benchmark.iterations` | `HarnessSettings.iterations` | overridable per rule; unset → Jetpack default (`50`, confirmed in capabilities.md §6) |
| Warmup iterations | `WarmupManager` fast/slow moving-average convergence | `HarnessSettings.warmupIterations` | override is a cap on top of Jetpack's own convergence detector, not a replacement for it |
| Profiling mode | `androidx.benchmark.profiling.mode` | `HarnessSettings.profiling` (`none`/`MethodTracing`/`StackSampling`) | androidx defaults to `MethodTracing` for a null config; `--device` passes `profiling.mode=None` so `none` is off; adds overhead — don't combine with the run used for the timed comparison (capabilities.md §4) |
| Compilation mode | AOT-by-default (library/AGP version gated) | not modeled — **no action needed** | confirmed already active on this repo's pinned versions (`benchmark-junit4:1.5.0`, AGP `8.13.2`); see capabilities.md §2 |
| Clock lock | `./gradlew lockClocks` (rooted/userdebug only) | **not invoked, no stated position** | open gap — highest-value knob for CPU-bound crypto timing, not yet decided one way or the other (capabilities.md §3, §8) |
| Minification | AGP `buildTypes.release` | `minifyEnabled false` (`modules/android/build.gradle`) | open gap — AndroidX guidance and GOMES both run benchmarks against minified release; this repo currently doesn't |
| Sustained performance mode | `Window.setSustainedPerformanceMode()` | on by Jetpack default | recorded as `context.sustainedPerformanceModeEnabled` |
| Thermal throttle handling | automatic pause + retry | not a repo setting | `thermalThrottleSleepSeconds` surfaced per-case, summed in `JetpackResults.runtime()` |
| Dead-code elimination guard | `BlackHole.consume()` | `run/BlackHole.kt`, called on every `measure()` | applies uniformly, not parameterized |
| Timed region boundary | none inside the loop: keys and IV pools are built before `measureRepeated` | `Invocations.of(prepared)` in `CryptoBenchmark.measure()` | a per-iteration `runWithMeasurementDisabled` cost ~40 ns/op on a Pixel 10 (SHA-256 697 → 659 ns once removed), so it is not used |

---

## Table B — Target-specific configuration

Varies per `PreparedCase` / `BenchmarkCase`.

| Dimension | Varies by | Values in scope | Source of truth |
|---|---|---|---|
| Algorithm | primitive | AES, ChaCha20, RSA, SHA-1/256/512, HmacSHA1/256, ECDSA, ... | `docs/cryptography/primitives.md` |
| Provider | algorithm × hardware | AndroidOpenSSL, AndroidKeyStore(+BCWorkaround) | `docs/cryptography/providers.md` |
| Key length (`key_len`) | algorithm | AES 128/192/256; RSA 2048/4096 (StrongBox: 2048 only); ECDSA P-256 (StrongBox: P-256 only); DESEDE 112/168 | `primitives.md` §Key sizes |
| Mode/padding | cipher | GCM/CBC/CTR/ECB × NoPadding/PKCS5Padding | `primitives.md` List table |
| Input size | operation | 64 B – 1 MB sweep | `docs/benchmark-methodology.md` (Downloads draft §3.2) |
| Operation | primitive | encrypt/decrypt/sign/verify/digest/keygen | `BenchmarkCase.operation` |
| Case identity | every combination | `caseId` string, drives `@Parameterized.Parameters(name = "{0}")` | `PreparedCase` |

Per-rule overrides of the target-specific dimensions above (`keySizes`, `inputSizes`, `operations`,
`parameters`, `key`) go through `testset/dto/Override.kt`, matched by `Rule`. `Override.harness`
lets a rule also override Table A's global settings for the cases it matches — e.g. running one
algorithm at a higher iteration count without changing the global default.

---

## Statistical methods (already decided — pointer, not duplicated here)

The statistics side of this project (median as primary statistic, IQR/p50/p90/p99 for dispersion,
CoV as a stability gate not a comparison metric, Mann–Whitney U / Wilcoxon for pairwise
comparison, Tukey-fence outlier handling) is already documented in
[`benchmark-methodology.md`](benchmark-methodology.md) §Statistical methods, and cross-validated
against three independent sources (this repo's own doc, the Downloads/Capstone Feb-2026 draft
§5.2, and the Desktop/capstone May-2026 abstract's fuller six-layer pipeline — see the
`capstone-docs-are-the-methodology` project memory for how those three relate). Not repeated here
to avoid drift between two copies of the same conclusion; this file is configuration only.

The one open item carried over from that discussion: whether the default iteration count (`50`,
Table A) gives Mann-Whitney U enough samples. Partial answer in
[jetpack-microbenchmark-capabilities.md §11](jetpack-microbenchmark-capabilities.md#11-harness-mechanics-from-the-capstone-papers---reconcile-dont-port):
the *Statistically Rigorous Android Macrobenchmarks* blog puts the floor at >30 iterations, which
the default clears — but confirm this is still true if `HarnessSettings.iterations` is ever
overridden downward for a fast-iterating dev loop.
