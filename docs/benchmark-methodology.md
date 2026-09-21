# Benchmark methodology notes

## Tool vs Paper

| Tool | Paper |
|---|---|
| /environment | /benchmark |
| /configuration | /analysis |
| / pre-prepareness | |

## Target

Cryptography primitives (FOcus on primitives)

| Bucket | Primitives (current BenchmarkScope.TYPES) | Gaps not yet in scope |
|---|---|---|
| Asymmetric | Signature, KeyPairGenerator, KeyAgreement | RSA/EC p 255 |
| Symmetric | Cipher (symmetric modes), KeyGenerator, Mac | AES |
| Other 'Primitives' | MessageDigest | HMAC-based KDFs, SecureRandom |
| KeyGeneration | KeyGenerator (symmetric), KeyPairGenerator (asymmetric) | |
| Other | — | KDF (SecretKeyFactory: PBKDF2/HKDF), SecureRandom throughput |

Source: 7 types currently in scope.

## Key store

Providers Security.getProviders() / ProviderProbe already surface on Android:

| Provider | Layer | Notes |
|---|---|---|
| AndroidKeyStore | hardware | TEE-backed vs StrongBox-backed. Device dependent |
| AndroidOpenSSL (Conscrypt) | software | BoringSSL-based. |

### Notes

Keystore layer differences to characterize:

- AndroidKeyStore (hardware, TEE/StrongBox split)
- Conscrypt / AndroidOpenSSL (software)

## Metric

| Category | Metric |
|---|---|
| Throughput | MB/s AND ops/sec |
| Latency | ns/op |
| Key generation | ts(keygen/keypair-gen) |
| Memory | allocation count (Jetpack Microbenchmark tracks natively) |
| warm | Jetpack |
| Energy | Perfectto + emanfa |

## Statistical methods

- Median as primary reported statistic (not mean). Timing distributions are right-skewed
- Coefficient of variation as a stability gate before trusting the median
- Report p50/p90/p99, not just one point estimate

---

- Comparisons between algorithms/providers: CI on the difference, or Mann–Whitney U (non-parametric).
- Outlier handling: Tukey fences (IQR-based), consistent with what Jetpack Microbenchmark does internally

---

- Environment capture (device/runtime/provider versions) before every run controls for the Mytkowicz "wrong data" environmental-bias problem; this is exactly what the discovery/capture module already does

## Jetpack Microbenchmark

What the library gives us for free, mapped to the Metric / Statistical methods sections above.

| Feature | Supports |
|---|---|
| Reports mean, median, standard deviation, and coefficient of variation across runs, plus the raw per-iteration runs. | Statistical methods  median-as-primary, CoV gate, and percentiles can all be computed per raw not jut aggregated (fine-grained control) |
| WarmupManager  runs until fast/slow moving averages converge before measuring | IDK how it works but will trust it |
| Automatic thermal-throttle detection, pauses and retries when device heats up | controls the systematic-bias source. |
| `./gradlew lockClocks`.  locks CPU clocks on rooted ("userdebug") devices | Reduce cpu frequency variances |
| `Window.setSustainedPerformanceMode()`, on by default. | Reduce cpu frequency variances. |
| Allocation count per iteration, reported alongside timing | Metric : memory, for free, no separate harness |
| `androidx.benchmark.profiling.mode=MethodTracing` / `StackSampling`(simpleperf) / `None` | lets us pull a profile on the same run that produced the metric, without a second harness |
| `androidx.benchmark.dryRunMode.enable` | fast presubmit/CI validation pass, decouples "does it run" from "is it statistically valid" |
| Full context block in `benchmarkData.json` (device, CPU core count, clock-lock status, memory) | this is the environment-capture control from Statistical methods above  Jetpack does its own version of what our discovery module already does independently |

## Open question

does benchmarkData.json's raw runs array give us enough samples per primitive to run Mann–Whitney U across algorithms, or do we need a higher iterations/measureRepeated count than the default for that to be meaningful — check once we're at the comparison stage, not blocking discovery work.

## Loose notes

- I feel like we try to somemwhat group different things or highly coupled things into one group
- SOme algorithm => runs really fast. Maybe too fast => so we have to validate the test results first. Batchinga analysis

## References

- eBACS / SUPERCOP: https://bench.cr.yp.to/
- eBACS methodology slides (2024): https://cr.yp.to/talks/2024.09.09/slides-djb-20240909-ebacs-4x3.pdf
- pqm4 NIST PQC benchmarking paper (2024): https://csrc.nist.gov/csrc/media/Events/2024/fifth-pqc-standardization-conference/documents/papers/pqm4-benchmarking-nist-addl-pq-sig-schemes.pdf
- Systematic Timing Leakage Analysis of NIST PQDSS Candidates (2025): https://arxiv.org/pdf/2509.04010
- Comparative Performance Evaluation of Kyber, sntrup761, FrodoKEM (2025): https://arxiv.org/pdf/2508.10023
- Jetpack Microbenchmark overview: https://developer.android.com/topic/performance/benchmarking/microbenchmark-overview
- Microbenchmark instrumentation arguments: https://developer.android.com/topic/performance/benchmarking/microbenchmark-instrumentation-args
- Profile a Microbenchmark (profiling.mode, simpleperf): https://developer.android.com/topic/performance/benchmarking/microbenchmark-profile
- Benchmarking in AndroidX (lockClocks, CI): https://android.googlesource.com/platform/frameworks/support/+/androidx-main/docs/benchmarking.md
- Statistically Rigorous Android Macrobenchmarks: https://blog.p-y.wtf/statistically-rigorous-android-macrobenchmarks
