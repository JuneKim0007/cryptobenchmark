package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.budget.NativeCleanup
import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import io.github.junekim0007.cryptobench.benchmark.report.MetricKeys
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import org.junit.Assert.assertEquals
import org.junit.Test
import org.yaml.snakeyaml.Yaml
import java.io.File

class JetpackResultsTest {

    private val example = File("example")

    private fun data() = File(example, "benchmark_jetpack_example.json").readText()

    private fun plan() = File(example, "benchmark_prepared_example.yaml").readText()

    private val converted = JetpackResults.convert(data(), plan())

    private val digest = converted.rows.single { it.algorithm == "SHA-256" }

    @Test
    fun convertingAgainWithAllocationRecoversWhatAndroidxAlreadyMeasured() {
        val timeOnly = plan().replace(Regex("metrics: \\[[^]]*]"), "metrics: [TIME]")
        val again = JetpackResults.convert(data(), timeOnly, metrics = listOf("TIME", "ALLOCATION"))
        assertEquals(setOf(MetricSamples.TIME, MetricSamples.ALLOCATIONS), again.rows.single { it.algorithm == "SHA-256" }.metrics.keys)
        JetpackResults.convert(data(), timeOnly).rows.forEach { row -> assertEquals(setOf(MetricSamples.TIME), row.metrics.keys) }
    }

    @Test
    fun theVariantComesFromThePlanAndIsNullWhenThePlanHasNone() {
        assertEquals("fixed", digest.variant)
        val notFixed = JetpackResults.convert(data(), plan().replaceFirst("  variant: fixed\n", "  variant: notFixed\n"))
        assertEquals(listOf("notFixed", "fixed"), notFixed.rows.map { it.variant })
        val scoped = JetpackResults.convert(data(), plan().replace("  variant: fixed\n", ""))
        assertEquals(listOf(null, null), scoped.rows.map { it.variant })
    }

    @Test
    fun aCasesPausedCleanupsFromTheDeviceFileReachItsRowAndTheWrittenFile() {
        val cleanups = JetpackResults.cleanupsOf("\"${digest.id}\": {everyCalls: 50000, cleanups: 4, pausedNanos: 812345}\n")
        val joined = JetpackResults.convert(data(), plan(), cleanups = cleanups).rows
        assertEquals(NativeCleanup(50_000, 4, 812_345), joined.single { it.id == digest.id }.cleanup)
        assertEquals(listOf(null), joined.filter { it.id != digest.id }.map { it.cleanup }.distinct())
        val written = BenchmarkJson(File("build")).text(converted.runtime, joined)
        assertEquals(NativeCleanup(50_000, 4, 812_345), CaseDocument.sections(CaseDocument.load(written)["cases"]).single { it["id"] == digest.id }
            .let { NativeCleanup.read(it[NativeCleanup.FIELD]) })
    }

    @Test
    fun aPlanCaseWithoutResolvedParametersIsDroppedWithItsReason() {
        val old = File(example, "benchmark_prepared_example.yaml").readText().replaceFirst(Regex("  resolvedParameters: .*\n"), "")
        val converted = JetpackResults.convert(File(example, "benchmark_jetpack_example.json").readText(), old)
        assertEquals(true, converted.dropped.first().startsWith("not_converted: MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM_fixed: missing_field: resolvedParameters"))
        assertEquals(1, converted.rows.size)
    }

    @Test
    fun aMetricThePlanAskedForButAndroidxDidNotWriteDropsThatCaseOnly() {
        val both = plan().replace("metrics: [TIME]", "metrics: [TIME, ALLOCATION]")
        val converted = JetpackResults.convert(data(), both)
        val lost = converted.dropped.single { it.startsWith("not_converted") }
        assertEquals(true, lost.startsWith("not_converted: Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4_fixed: missing_field: metrics.allocationCount"))
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
                "no_metrics: MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM_fixed",
                "no_metrics: Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4_fixed",
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
    fun theConvertedFileIsWhatTheAnalysisReads() {
        val text = BenchmarkJson(example).text(converted.runtime, converted.rows)
        // compared parsed: key order and spacing are not what the analysis reads
        assertEquals(
            Yaml().load<Any>("""{
  "runtime": {"model": "Pixel 9", "fingerprint": "google/tokay/tokay:16/BP3A.250905.014/13718934:user/release-keys", "sdkInt": "36", "jetpackCpuLocked": "false", "sustainedPerformanceModeEnabled": "true", "compilationMode": "DEFAULT", "thermalThrottleSleepSeconds": "90"},
  "cases": [
    {"id": "MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM_fixed", "type": "MessageDigest", "algorithm": "SHA-256", "provider": "AndroidOpenSSL", "operation": "DIGEST", "keySize": null, "inputSize": 1024, "keyKind": "none", "variant": "fixed", "parameters": {}, "thermalThrottleSleepSeconds": 0,
     "metrics": {"timeNs": {"iterations": 8192, "runs": [1191.0, 1180.0, 1256.0, 1188.0, 1193.0], "reported": {"minimum": 1180.0, "maximum": 1256.0, "median": 1191.0, "coefficientOfVariation": 0.019}}, "allocationCount": {"iterations": 1, "runs": [2.0, 2.0, 3.0, 2.0, 2.0], "reported": {"minimum": 2.0, "maximum": 3.0, "median": 2.0, "coefficientOfVariation": 0.183}}}},
    {"id": "Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4_fixed", "type": "Cipher", "algorithm": "AES/GCM/NoPadding", "provider": "AndroidOpenSSL", "operation": "ENCRYPT", "keySize": 128, "inputSize": 1024, "keyKind": "secret", "variant": "fixed", "parameters": {"mode": "GCM", "padding": "NoPadding", "ivBytes": 12, "tagBits": 128, "keyBits": 128}, "thermalThrottleSleepSeconds": 90,
     "metrics": {"timeNs": {"iterations": 4096, "runs": [2401.0, 2380.0, 2611.0, 2396.0, 2410.0], "reported": {"minimum": 2380.0, "maximum": 2611.0, "median": 2401.0, "coefficientOfVariation": 0.031}}}}
  ]
}
"""),
            Yaml().load<Any>(text),
        )
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
    fun aSettingThatNeverReachedTheTimerIsReportedWhenTheFileIsConverted() {
        val plan = File(example, "benchmark_prepared_example.yaml").readText()
            .replaceFirst("  harness: {iterations: 5}\n  key: {kind: none}", "  harness: {iterations: 7}\n  key: {kind: none}")
        val audited = JetpackResults.convert(File(example, "benchmark_jetpack_example.json").readText(), plan)
        assertEquals(listOf("iterations_not_applied: MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM_fixed asked for 7, timeNs has 5 runs"), audited.notApplied)
    }

    private companion object {

        const val NO_METRICS = """
            {"context": {"build": {"model": "Pixel 9", "fingerprint": "f", "version": {"sdk": 36}},
                         "cpuLocked": false, "sustainedPerformanceModeEnabled": true, "compilationMode": "DEFAULT"},
             "benchmarks": [
               {"name": "measure[MessageDigest_SHA-256_DIGEST_AndroidOpenSSL_i1024_WARM_fixed]", "metrics": {},
                "repeatIterations": 8192, "thermalThrottleSleepSeconds": 0},
               {"name": "measure[Cipher_AES-GCM-NoPadding_ENCRYPT_AndroidOpenSSL_k128_i1024_WARM_p81667fe4_fixed]",
                "repeatIterations": 4096, "thermalThrottleSleepSeconds": 0}
             ]}
        """
    }
}
