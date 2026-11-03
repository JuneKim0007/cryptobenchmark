package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.ReportedStats
import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import io.github.junekim0007.cryptobench.benchmark.report.MetricKeys
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

class JetpackResultsTest {

    private val example = File("example")

    private fun data() = File(example, "benchmark_jetpack_example.json").readText()

    private fun plan() = File(example, "benchmark_prepared_example.yaml").readText()

    private val converted = JetpackResults.convert(data(), plan())

    private val digest = converted.rows.single { it.algorithm == "SHA-256" }

    @Test
    fun theResolvedParametersComeFromThePlan() {
        assertEquals(emptyMap<String, Any>(), digest.parameters)
        assertEquals(mapOf("mode" to "GCM", "padding" to "NoPadding", "ivBytes" to 12, "tagBits" to 128, "keyBits" to 128),
            converted.rows.single { it.type == "Cipher" }.parameters)
    }

    @Test
    fun aPlanCaseWithoutResolvedParametersIsDroppedWithItsReason() {
        val old = File(example, "benchmark_prepared_example.yaml").readText().replaceFirst(Regex("  resolvedParameters: .*\n"), "")
        val converted = JetpackResults.convert(File(example, "benchmark_jetpack_example.json").readText(), old)
        assertEquals("not_converted: MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM: missing_field: resolvedParameters for " +
            "MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM; prepared.yaml predates schemaVersion 2", converted.dropped.first())
        assertEquals(1, converted.rows.size)
    }

    @Test
    fun aCaseKeepsItsSamplesAndGetsItsShapeFromThePlan() {
        assertEquals("MessageDigest", digest.type)
        assertEquals("AndroidOpenSSL", digest.provider)
        assertEquals("DIGEST", digest.operation)
        assertEquals(null, digest.keySize)
        assertEquals(1024, digest.inputSize)
        assertEquals(listOf(1191.0, 1180.0, 1256.0, 1188.0, 1193.0), digest.time?.runs)
        assertEquals(8192, digest.time?.iterations)
        val encrypt = converted.rows.single { it.algorithm == "AES/GCM/NoPadding" }
        assertEquals(128, encrypt.keySize)
        assertEquals(4096, encrypt.time?.iterations)
    }

    @Test
    fun theAllocationMetricIsCarriedAlongsideTheTiming() {
        assertEquals(listOf(MetricSamples.TIME, MetricSamples.ALLOCATIONS), digest.metrics.keys.toList())
        assertEquals(listOf(2.0, 2.0, 3.0, 2.0, 2.0), digest.metrics[MetricSamples.ALLOCATIONS]?.runs)
        assertEquals(1, digest.metrics[MetricSamples.ALLOCATIONS]?.iterations)
    }

    @Test
    fun timeOnlyDropsTheAllocationPhaseAndroidxAlwaysRuns() {
        val timeOnly = plan().replace("metrics: [TIME, ALLOCATION]", "metrics: [TIME]")
        val written = CaseDocument.sections(CaseDocument.load(data())["benchmarks"]).first { "SHA-256" in it["name"].toString() }
        assertEquals(true, MetricSamples.ALLOCATIONS in CaseDocument.section(written["metrics"]))
        val row = JetpackResults.convert(data(), timeOnly).rows.single { it.algorithm == "SHA-256" }
        assertEquals(listOf(MetricSamples.TIME), row.metrics.keys.toList())
    }

    @Test
    fun aMetricThePlanAskedForButAndroidxDidNotWriteDropsThatCaseOnly() {
        val both = plan().replace("metrics: [TIME]", "metrics: [TIME, ALLOCATION]")
        val converted = JetpackResults.convert(data(), both)
        assertEquals(listOf("not_converted: Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4: missing_field: " +
            "metrics.allocationCount for Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4; androidx wrote [timeNs]"),
            converted.dropped.filter { it.startsWith("not_converted") })
        assertEquals(listOf("SHA-256"), converted.rows.map { it.algorithm })
    }

    @Test
    fun cpuEventsAreCarriedPerOperationUnderAndroidxsNames() {
        val counted = plan().replace("metrics: [TIME, ALLOCATION]", "metrics: [TIME, CPU_EVENTS]")
        val events = MetricKeys.CPU_EVENTS.joinToString("") { "\"$it\": {\"runs\": [10.0, 11.0]}, " }
        val written = data().replaceFirst("\"allocationCount\": {", "$events\"allocationCount\": {")
        val row = JetpackResults.convert(written, counted).rows.single { it.algorithm == "SHA-256" }
        assertEquals(listOf(MetricSamples.TIME) + MetricKeys.CPU_EVENTS, row.metrics.keys.toList())
        assertEquals(MetricSamples(listOf(10.0, 11.0), 8192), row.metrics.getValue("instructions"))
    }

    @Test
    fun aCaseWithNoMetricAtAllIsReported() {
        val nothing = JetpackResults.convert(NO_METRICS, File(example, "benchmark_prepared_example.yaml").readText())
        assertEquals(
            listOf(
                "no_metrics: MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM",
                "no_metrics: Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4",
            ),
            nothing.dropped,
        )
        assertEquals(emptyList<String>(), nothing.rows.map { it.id })
    }

    @Test
    fun aMeasurementWithNoCaseIsReported() {
        assertEquals(listOf("not_in_plan: Cipher_ChaCha20_ENCRYPT_AndroidOpenSSL_k256_i1024_WARM"), converted.dropped)
        assertEquals(2, converted.rows.size)
    }

    @Test
    fun theRuntimeCarriesWhatMakesTheNumbersJudgeable() {
        assertEquals(
            mapOf(
                "model" to "Pixel 9",
                "fingerprint" to "google/tokay/tokay:16/BP3A.250905.014/13718934:user/release-keys",
                "sdkInt" to "36",
                "jetpackCpuLocked" to "false",
                "sustainedPerformanceModeEnabled" to "true",
                "compilationMode" to "DEFAULT",
                "thermalThrottleSleepSeconds" to "90",
            ),
            converted.runtime,
        )
    }

    @Test
    fun theConvertedFileIsWhatTheAnalysisReads() {
        val text = BenchmarkJson(example).text(converted.runtime, converted.rows)
        assertEquals(
            """{
  "runtime": {"model": "Pixel 9", "fingerprint": "google/tokay/tokay:16/BP3A.250905.014/13718934:user/release-keys", "sdkInt": "36", "jetpackCpuLocked": "false", "sustainedPerformanceModeEnabled": "true", "compilationMode": "DEFAULT", "thermalThrottleSleepSeconds": "90"},
  "cases": [
    {"id": "MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM", "type": "MessageDigest", "algorithm": "SHA-256", "provider": "AndroidOpenSSL", "operation": "DIGEST", "keySize": null, "inputSize": 1024, "keyKind": "none", "parameters": {},
     "metrics": {"timeNs": {"iterations": 8192, "runs": [1191.0, 1180.0, 1256.0, 1188.0, 1193.0], "reported": {"minimum": 1180.0, "maximum": 1256.0, "median": 1191.0, "coefficientOfVariation": 0.019}}, "allocationCount": {"iterations": 1, "runs": [2.0, 2.0, 3.0, 2.0, 2.0], "reported": {"minimum": 2.0, "maximum": 3.0, "median": 2.0, "coefficientOfVariation": 0.183}}}},
    {"id": "Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4", "type": "Cipher", "algorithm": "AES/GCM/NoPadding", "provider": "AndroidOpenSSL", "operation": "ENCRYPT", "keySize": 128, "inputSize": 1024, "keyKind": "secret", "parameters": {"mode": "GCM", "padding": "NoPadding", "ivBytes": 12, "tagBits": 128, "keyBits": 128},
     "metrics": {"timeNs": {"iterations": 4096, "runs": [2401.0, 2380.0, 2611.0, 2396.0, 2410.0], "reported": {"minimum": 2380.0, "maximum": 2611.0, "median": 2401.0, "coefficientOfVariation": 0.031}}}}
  ]
}
""",
            text,
        )
    }

    @Test
    fun theLibrarysOwnStatisticsAreCarriedAlongsideTheRuns() {
        assertEquals(ReportedStats(1180.0, 1256.0, 1191.0, 0.019), digest.time?.reported)
        assertEquals(ReportedStats(2.0, 3.0, 2.0, 0.183), digest.metrics[MetricSamples.ALLOCATIONS]?.reported)
    }

    @Test
    fun aFractionalSampleKeepsItsFraction() {
        val fractional = JetpackResults.convert(
            File(example, "benchmark_jetpack_example.json").readText().replace("1191.0, 1180.0, 1256.0", "1191.75, 1180.5, 1256.25"),
            File(example, "benchmark_prepared_example.yaml").readText(),
        ).rows.single { it.algorithm == "SHA-256" }
        assertEquals(listOf(1191.75, 1180.5, 1256.25), fractional.time?.runs?.take(3))
    }

    @Test
    fun aPartialSetOfStatisticsIsNotCarried() {
        assertEquals(null, CaseDocument.reportedStats(mapOf("minimum" to 1.0, "median" to 2.0)))
        assertEquals(null, CaseDocument.reportedStats(null))
    }

    @Test
    fun aPlanWhoseIterationsMatchTheRunsIsSilent() {
        assertEquals(emptyList<String>(), converted.notApplied)
    }

    @Test
    fun aSettingThatNeverReachedTheTimerIsReportedWhenTheFileIsConverted() {
        val plan = File(example, "benchmark_prepared_example.yaml").readText()
            .replaceFirst("  harness: {iterations: 5}\n  key: {kind: none}", "  harness: {iterations: 7}\n  key: {kind: none}")
        val audited = JetpackResults.convert(File(example, "benchmark_jetpack_example.json").readText(), plan)
        assertEquals(listOf("iterations_not_applied: MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM asked for 7, timeNs has 5 runs"), audited.notApplied)
    }

    private companion object {

        const val NO_METRICS = """
            {"context": {"build": {"model": "Pixel 9", "fingerprint": "f", "version": {"sdk": 36}},
                         "cpuLocked": false, "sustainedPerformanceModeEnabled": true, "compilationMode": "DEFAULT"},
             "benchmarks": [
               {"name": "measure[MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM]", "metrics": {},
                "repeatIterations": 8192, "thermalThrottleSleepSeconds": 0},
               {"name": "measure[Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4]",
                "repeatIterations": 4096, "thermalThrottleSleepSeconds": 0}
             ]}
        """
    }
}
